# LangChain Integration for SafeSheet

This document describes the LangChain integration added to SafeSheet for enhanced SQL validation.

## Overview

The LangChain integration provides an alternative validation method using Large Language Models (LLMs) to generate comprehensive safety reports with risk assessment and rollback scripts.

## Architecture

### Backend Components

1. **`backend/langchain_validator.py`**
   - Implements LangChain LCEL (LangChain Expression Language) chain
   - Uses `ChatOpenAI` or `ChatAnthropic` models
   - Integrates DuckDB for SQL syntax validation
   - Generates JSON responses with risk_level, warnings, and rollback_sql

2. **`backend/main.py`**
   - New endpoint: `POST /validate-sql`
   - Accepts SQL string and returns LangChain validation results

### Frontend Components

1. **`frontend/src/components/LangChainReport.jsx`**
   - New component to display LangChain validation results
   - Shows risk level, warnings, DuckDB validation, and rollback SQL

2. **`frontend/src/services/api.js`**
   - New function: `validateSQL()` to call the LangChain endpoint

3. **`frontend/src/App.jsx`**
   - Toggle option to use LangChain validation
   - Integrated UI to switch between traditional and LangChain analysis

## LangChain LCEL Chain

The chain is built using LangChain Expression Language:

```python
chain = (
    prompt
    | llm
    | json_parser
)
```

### Chain Components

1. **Prompt Template**: System and human messages with:
   - Mock database schema as context
   - Instructions for risk assessment
   - JSON output format specification

2. **LLM**: ChatOpenAI (GPT-4o) or ChatAnthropic (Claude 3.5 Sonnet)

3. **Output Parser**: JsonOutputParser to ensure valid JSON response

## DuckDB Integration

Before sending to LLM, SQL is validated using DuckDB:

- Syntax validation
- Dry-run execution attempt
- Error capture for LLM context

## API Endpoint

### POST `/validate-sql`

**Request:**
```json
{
  "sql": "UPDATE users SET status = 'inactive'"
}
```

**Response:**
```json
{
  "success": true,
  "risk_level": "Medium",
  "warnings": [
    "⚠️  CRITICAL: This UPDATE statement lacks a WHERE clause..."
  ],
  "rollback_sql": "UPDATE users SET status = 'active' WHERE status = 'inactive';",
  "duckdb_validation": {
    "syntax_valid": true,
    "dry_run_successful": false,
    "error": null
  }
}
```

## Usage

### Backend Setup

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Set API key in `.env`:
```
OPENAI_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=your_key_here
```

3. Start backend:
```bash
python main.py
```

### Frontend Usage

1. Toggle "Use LangChain Validation" checkbox
2. Enter SQL in the editor
3. Click "Analyze SQL"
4. View LangChain-generated safety report

## Mock Schema

The mock schema provides context to the LLM about database structure:

```
- users (id, name, email, status, created_at)
- orders (id, user_id, total, status, created_at)
- products (id, name, price, stock)
- logs (id, message, level, timestamp)
- temp_data (id, data)
```

## Benefits

1. **LLM-Powered Analysis**: More nuanced risk assessment using AI
2. **Context-Aware**: Uses mock schema for better understanding
3. **DuckDB Validation**: Catches syntax errors before LLM processing
4. **Structured Output**: JSON format ensures consistent responses
5. **Flexible**: Supports both OpenAI and Anthropic models

## Configuration

The system automatically detects available API keys and uses the appropriate provider:
- Checks for `OPENAI_API_KEY` first
- Falls back to `ANTHROPIC_API_KEY`
- Raises error if neither is available

## Error Handling

- DuckDB validation errors are captured and included in LLM context
- LLM errors are caught and returned in response
- Invalid JSON responses are handled gracefully

