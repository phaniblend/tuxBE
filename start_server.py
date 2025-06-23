#!/usr/bin/env python3
"""
Simple startup script for TUX backend
Bypasses any import issues and starts the server directly
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("PORT", "8000")

def main():
    """Start the FastAPI server"""
    try:
        print("🚀 Starting TUX Backend Server...")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🐍 Python version: {sys.version}")
        
        # Start server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 