"""LangChain-based SQL validator using LCEL."""

import json
import os
from typing import Dict, Any, Optional
import duckdb
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
import sys
from pathlib import Path

# Add parent directory to path to import safesheet
sys.path.insert(0, str(Path(__file__).parent.parent))
from safesheet.config import Config

# Try to import LLM providers
try:
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from langchain_anthropic import ChatAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Mock schema for context
MOCK_SCHEMA = """
Database Schema:
- users (id: INTEGER, name: VARCHAR, email: VARCHAR, status: VARCHAR, created_at: TIMESTAMP)
- orders (id: INTEGER, user_id: INTEGER, total: DECIMAL, status: VARCHAR, created_at: TIMESTAMP)
- products (id: INTEGER, name: VARCHAR, price: DECIMAL, stock: INTEGER)
- logs (id: INTEGER, message: TEXT, level: VARCHAR, timestamp: TIMESTAMP)
- temp_data (id: INTEGER, data: TEXT)
"""


def get_llm():
    """Get the appropriate LLM based on available API keys."""
    provider = Config.get_llm_provider()
    
    if provider == "deepseek" and OPENAI_AVAILABLE:
        api_key = Config.get_deepseek_api_key()
        endpoint = Config.get_deepseek_endpoint()
        model = Config.get_deepseek_model()
        if api_key:
            return ChatOpenAI(
                model=model,
                temperature=0.1,
                api_key=api_key,
                base_url=endpoint
            )
    
    elif provider == "openai" and OPENAI_AVAILABLE:
        api_key = Config.get_openai_api_key()
        if api_key:
            return ChatOpenAI(
                model="gpt-4o",
                temperature=0.1,
                api_key=api_key
            )
    
    elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
        api_key = Config.get_anthropic_api_key()
        if api_key:
            return ChatAnthropic(
                model="claude-3-5-sonnet-20241022",
                temperature=0.1,
                api_key=api_key
            )
    
    raise ValueError("No LLM provider available. Please set DEEPSEEK_API_KEY, OPENAI_API_KEY or ANTHROPIC_API_KEY")


def validate_sql_with_duckdb(sql: str) -> Dict[str, Any]:
    """Validate SQL syntax using DuckDB."""
    result = {
        "syntax_valid": False,
        "error": None,
        "dry_run_successful": False
    }
    
    try:
        # Create in-memory DuckDB connection
        conn = duckdb.connect(":memory:")
        
        # Try to execute the SQL (this will catch syntax errors)
        try:
            conn.execute(sql)
            result["syntax_valid"] = True
            result["dry_run_successful"] = True
        except Exception as e:
            result["syntax_valid"] = False
            result["error"] = str(e)
            # Some SQL statements (like DDL) might not execute but are still valid
            # Check if it's a syntax error vs execution error
            error_str = str(e).lower()
            if "syntax" in error_str or "parse" in error_str:
                result["syntax_valid"] = False
            else:
                # Might be valid SQL but can't execute in empty DB
                result["syntax_valid"] = True
        
        conn.close()
    except Exception as e:
        result["error"] = f"DuckDB validation error: {str(e)}"
    
    return result


def create_validation_chain() -> RunnableSequence:
    """Create LangChain LCEL chain for SQL validation."""
    
    # Get LLM
    llm = get_llm()
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Database Engineer specializing in SQL safety analysis.

Your task is to analyze SQL statements and generate a comprehensive safety report.

Context:
{mock_schema}

Analyze the following SQL statement and provide a JSON response with:
1. risk_level: "Low", "Medium", or "High"
   - Low: SELECT statements (read-only)
   - Medium: UPDATE, DELETE, INSERT statements
   - High: ALTER, DROP, TRUNCATE statements
2. warnings: Array of warning strings explaining potential risks
   - Flag missing WHERE clauses in UPDATE/DELETE
   - Flag DDL operations that modify structure
   - Flag operations that affect all rows
3. rollback_sql: SQL script to undo the operation (idempotent)
   - For UPDATE: Generate UPDATE to restore previous values
   - For DELETE: Generate INSERT to restore deleted rows (if possible)
   - For INSERT: Generate DELETE to remove inserted rows
   - For DDL: Provide restoration script or backup recommendation

Return ONLY valid JSON, no markdown formatting."""),
        ("human", "SQL Statement:\n```sql\n{sql}\n```\n\nDuckDB Validation:\n{duckdb_result}")
    ])
    
    # Create JSON parser
    json_parser = JsonOutputParser()
    
    # Build the chain using LCEL
    chain = (
        prompt
        | llm
        | json_parser
    )
    
    return chain


async def validate_sql_with_langchain(sql: str) -> Dict[str, Any]:
    """Validate SQL using LangChain LCEL chain."""
    
    # First, validate SQL syntax with DuckDB
    duckdb_result = validate_sql_with_duckdb(sql)
    
    # Format DuckDB result for prompt
    duckdb_result_str = json.dumps(duckdb_result, indent=2)
    
    # Create and run the chain
    chain = create_validation_chain()
    
    try:
        result = await chain.ainvoke({
            "sql": sql,
            "mock_schema": MOCK_SCHEMA,
            "duckdb_result": duckdb_result_str
        })
        
        # Ensure result has required fields
        if not isinstance(result, dict):
            raise ValueError("LLM did not return a valid JSON object")
        
        # Add DuckDB validation info
        result["duckdb_validation"] = duckdb_result
        
        return {
            "success": True,
            "risk_level": result.get("risk_level", "Unknown"),
            "warnings": result.get("warnings", []),
            "rollback_sql": result.get("rollback_sql", ""),
            "duckdb_validation": duckdb_result
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "duckdb_validation": duckdb_result
        }

