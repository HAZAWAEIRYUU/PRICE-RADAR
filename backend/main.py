from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from database import engine
import models
from routes import auth, products, prices, plan, stripe_api, notifications
import os
import uuid
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Contextvar-based request_id wiring. Each request gets a unique ID that
# downstream log statements can pick up via the filter below. That makes
# multi-step flows (auth → product create → scrape → notify) reconstructable.
import contextvars
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class _RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id_var.get()
        return True


logging.basicConfig(
    level=logging.INFO if os.environ.get("DATABASE_URL") else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] [%(request_id)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_req_filter = _RequestIdFilter()
for _h in logging.getLogger().handlers:
    _h.addFilter(_req_filter)
logger = logging.getLogger("priceradar")

import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper.tasks import run_scheduled_scraping, cleanup_old_history

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create DB tables (idempotent fallback for local SQLite dev; production uses Alembic)
models.Base.metadata.create_all(bind=engine)
logger.info("Database tables initialized")

# Scheduler setup
scheduler = AsyncIOScheduler()
scheduler.add_job(run_scheduled_scraping, "interval", hours=1)
scheduler.add_job(cleanup_old_history, "interval", hours=24)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting background scheduler")
    scheduler.start()
    yield
    # Shutdown
    logger.info("Shutting down background scheduler")
    scheduler.shutdown()

app = FastAPI(title="Price-Radar API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def _request_id_middleware(request: Request, call_next):
    incoming = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    rid = incoming if (incoming and len(incoming) <= 64) else uuid.uuid4().hex[:16]
    token = _request_id_var.set(rid)
    try:
        response = await call_next(request)
    finally:
        _request_id_var.reset(token)
    response.headers["X-Request-ID"] = rid
    return response

# Configure CORS
_prod_origin_regex = r"https://(www\.)?priceradar\.space|https://([a-z0-9-]+\.)?price-radar\.pages\.dev"
_dev_origins = [
    "http://localhost:3000",
    "http://localhost:3333",
    "http://localhost:53430",
]
_is_production = bool(os.environ.get("DATABASE_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_prod_origin_regex,
    allow_origins=[] if _is_production else _dev_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(prices.router, prefix="/api", tags=["prices"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(stripe_api.router, prefix="/api/stripe", tags=["stripe"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Price-Radar API"}


@app.get("/health")
def health():
    """Liveness probe — returns 200 unless the process is unhealthy."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness probe — fails if the DB is unreachable, so the load
    balancer can drain a crashing instance instead of serving 500s.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Readiness check failed: %s", e)
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ready"}
