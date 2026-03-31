from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
import models
from routes import auth, products, prices, plan, stripe_api

# Create DB tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price-Radar API")

# Configure CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3333",
    "http://localhost:53430",
    "https://priceradar.space",
    "https://www.priceradar.space",
    "https://price-radar.pages.dev",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(prices.router, prefix="/api", tags=["prices"])
app.include_router(plan.router, prefix="/api", tags=["plan"])
app.include_router(stripe_api.router, prefix="/api/stripe", tags=["stripe"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Price-Radar API"}
