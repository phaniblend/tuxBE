#!/usr/bin/env python3
"""
Quick start server for TUX backend
Minimal dependencies to get the server running
"""

import os
import sys
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal FastAPI app
app = FastAPI(title="TUX API", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "TUX API is running!", "status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "TUX Backend"}

@app.get("/api/test")
async def test():
    return {"message": "API is working!", "timestamp": "2024-01-01"}

if __name__ == "__main__":
    print("🚀 Starting TUX Backend (Quick Start)...")
    print("📁 Working directory:", os.getcwd())
    print("🐍 Python version:", sys.version)
    print("🌐 Using port 8001 to avoid conflicts")
    
    try:
        uvicorn.run(
            "quick_start:app",
            host="0.0.0.0",
            port=8001,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1) 