from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import cleaning, mapping, segmentation, upload

app = FastAPI(
    title="Customer Segmentation API",
    description="Upload transaction data and segment customers using RFM, ABC, or LRFMS.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(mapping.router)
app.include_router(cleaning.router)
app.include_router(segmentation.router)


@app.get("/health")
def health():
    return {"status": "ok"}
