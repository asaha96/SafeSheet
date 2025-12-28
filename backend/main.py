"""FastAPI backend for SafeSheet web interface."""

import sys
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add parent directory to path to import safesheet
sys.path.insert(0, str(Path(__file__).parent.parent))

from safesheet import analyze_sql, SafetyReport

app = FastAPI(
    title="SafeSheet API",
    description="API for SQL safety analysis and rollback generation",
    version="0.1.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SQLAnalysisRequest(BaseModel):
    """Request model for SQL analysis."""
    sql: str
    include_rollback: bool = True
    include_dry_run: bool = True
    sample_data: Optional[Dict[str, list]] = None


class SQLAnalysisResponse(BaseModel):
    """Response model for SQL analysis."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "SafeSheet API",
        "version": "0.1.0",
        "endpoints": {
            "/analyze": "POST - Analyze SQL statement",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze", response_model=SQLAnalysisResponse)
async def analyze_sql_endpoint(request: SQLAnalysisRequest):
    """Analyze SQL statement and return safety report."""
    try:
        if not request.sql or not request.sql.strip():
            raise HTTPException(status_code=400, detail="SQL statement cannot be empty")
        
        # Generate safety report
        report = analyze_sql(
            sql=request.sql,
            include_rollback=request.include_rollback,
            include_dry_run=request.include_dry_run,
            sample_data=request.sample_data
        )
        
        return SQLAnalysisResponse(
            success=True,
            data=report
        )
    
    except ValueError as e:
        return SQLAnalysisResponse(
            success=False,
            error=f"SQL parsing error: {str(e)}"
        )
    except Exception as e:
        return SQLAnalysisResponse(
            success=False,
            error=f"Error analyzing SQL: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

