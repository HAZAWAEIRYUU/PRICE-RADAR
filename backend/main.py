from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import engine
import models
from routes import auth, products, prices, plan, stripe_api, notifications
import os
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure structured logging
logging.basicConfig(
    level=logging.INFO if os.environ.get("DATABASE_URL") else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
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
