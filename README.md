# SafeSheet 🛡️

> A safety-first SQL tool that prevents accidental data loss and automates SQL rollbacks.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

SafeSheet is a comprehensive SQL safety analysis tool designed for data engineers and database administrators. It automatically analyzes SQL statements, assesses risk levels, generates rollback scripts, and simulates changes before execution.

## ✨ Features

- **🔍 SQL Parsing**: Uses `sqlglot` to identify impact radius (affected tables/columns)
- **⚠️ Risk Assessment**: Automatically flags high-risk operations (ALTER, DROP, TRUNCATE)
- **🔄 Rollback Generation**: Uses LLM (Claude 3.5 or GPT-4o) to generate idempotent inverse SQL scripts
- **🤖 LangChain Integration**: Alternative AI-powered validation using LangChain LCEL chains for enhanced analysis
- **🧪 Dry Run**: Simulates SQL changes using in-memory DuckDB
- **📊 Safety Reports**: Comprehensive reports with risk levels, impact analysis, and rollback scripts
- **🎯 Explainability**: Every safety warning explains *why* it is dangerous
- **🌐 Web Interface**: Modern React frontend with SQL editor and visual reports
- **⚡ API**: FastAPI backend for programmatic access

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/asaha96/SafeSheet.git
cd SafeSheet

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### Configuration

Create a `.env` file in the project root with your LLM API key:

```bash
# For Anthropic Claude (recommended)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OR for OpenAI GPT-4
OPENAI_API_KEY=your_openai_api_key_here
```

> **Note**: Rollback generation and LangChain validation require an API key, but other features (parsing, risk assessment, dry-run) work without it.

## 📖 Usage

### Web Interface (Recommended)

**Start Backend:**
```bash
./start_backend.sh
# Or manually: cd backend && source ../venv/bin/activate && python main.py
```

**Start Frontend:**
```bash
./start_frontend.sh
# Or manually: cd frontend && npm run dev
```

Open `http://localhost:5173` in your browser!

**Toggle between analysis modes:**
- **Traditional Analysis**: Rule-based risk assessment with sqlglot parsing
- **LangChain Validation**: AI-powered analysis using LangChain LCEL chains (toggle checkbox in UI)

### Command Line Interface

#### Analyze a SQL file:
```bash
python -m safesheet analyze examples/example_queries.sql
```

#### Analyze SQL from command line:
```bash
python -m safesheet analyze --sql "UPDATE users SET status = 'inactive'"
```

#### Analyze SQL from stdin:
```bash
echo "DROP TABLE users" | python -m safesheet analyze
```

#### Dry-run only (no rollback generation):
```bash
python -m safesheet analyze --sql "UPDATE users SET status = 'active'" --no-rollback
```

#### Save report to file:
```bash
python -m safesheet analyze query.sql -o safety_report.txt
```

### Python API

```python
from safesheet import analyze_sql, SafetyReport

# Simple analysis
sql = "UPDATE users SET status = 'inactive'"
report = analyze_sql(sql, include_rollback=True, include_dry_run=True)

print(f"Risk Level: {report['risk_level']}")
print(f"Warnings: {report['warnings']}")
print(f"Rollback: {report['rollback_script']}")

# Using SafetyReport class for formatted output
report_gen = SafetyReport(sql, include_rollback=True)
report = report_gen.generate()
formatted = report_gen.format_report(report)
print(formatted)
```

## 📋 Example Output

```
================================================================================
SAFETY REPORT
================================================================================

SQL Statement:
--------------------------------------------------------------------------------
UPDATE users SET status = 'inactive'

Risk Level: ⚠️ Medium

Statement Type: UPDATE

Impact Analysis:
--------------------------------------------------------------------------------
  Tables Affected: 1
  Tables: users
  Columns Affected: 1
    - users: status
  Has WHERE Clause: False

Warnings:
--------------------------------------------------------------------------------
  ⚠️  CRITICAL: This UPDATE statement lacks a WHERE clause and will affect ALL rows in users.

Explanation:
--------------------------------------------------------------------------------
  Risk Level: Medium This UPDATE statement will affect ALL rows in users because it lacks a WHERE clause.

Rollback Script:
--------------------------------------------------------------------------------
-- Rollback: Restore previous status values
-- WARNING: This assumes you have a backup or can restore from logs
UPDATE users SET status = 'active' WHERE status = 'inactive';
```

## 🎯 Core Principles

1. **Safety First**: Never execute raw DDL/DML without validation
2. **Idempotency**: All generated SQL (including rollbacks) is repeatable without side effects
3. **Explainability**: Every safety warning explains *why* it is dangerous

## 📊 Risk Levels

- **🟢 Low**: SELECT (read-only) or INSERT statements
- **🟡 Medium**: UPDATE or DELETE statements
- **🔴 High**: ALTER, DROP, or TRUNCATE statements

## 🏗️ Architecture

```
SafeSheet/
├── safesheet/          # Core library
│   ├── parser.py              # SQL parsing with sqlglot
│   ├── risk_assessor.py       # Risk assessment engine
│   ├── rollback_generator.py  # LLM-powered rollback generation
│   ├── dry_run.py             # DuckDB simulation engine
│   ├── safety_report.py       # Report generator
│   └── cli.py                 # Command-line interface
├── backend/            # FastAPI backend
│   ├── main.py                 # API server
│   ├── langchain_validator.py # LangChain LCEL validation chain
│   └── requirements.txt
├── frontend/           # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── SQLEditor.jsx
│   │   │   ├── SafetyReport.jsx
│   │   │   └── LangChainReport.jsx
│   │   └── App.jsx
│   └── package.json
└── examples/           # Example queries and usage
```

## 🤖 What is LangChain Used For?

LangChain is used in SafeSheet to provide an **AI-powered alternative validation method** that complements the traditional rule-based analysis. Here's how it works:

### LangChain's Role:

1. **Structured AI Pipeline (LCEL Chain)**:
   - Creates a composable chain: `Prompt → LLM → JSON Parser`
   - Ensures consistent, structured output from the LLM

2. **Enhanced SQL Analysis**:
   - Takes SQL statement + database schema context
   - Sends to LLM (GPT-4o or Claude 3.5) for intelligent analysis
   - Generates risk assessment, warnings, and rollback scripts

3. **DuckDB Integration**:
   - Validates SQL syntax with DuckDB before LLM processing
   - Includes validation results in the prompt for better context

4. **Structured Output**:
   - Uses `JsonOutputParser` to ensure the LLM returns valid JSON
   - Returns: `risk_level`, `warnings[]`, and `rollback_sql`

### Why Use LangChain?

- **More Nuanced Analysis**: LLMs can understand context and provide more sophisticated risk assessments
- **Better Rollback Scripts**: AI can generate more accurate rollback SQL based on understanding the operation
- **Schema-Aware**: Uses mock database schema to provide better context to the LLM
- **Flexible**: Easy to switch between OpenAI and Anthropic models

### Traditional vs LangChain:

| Feature | Traditional Analysis | LangChain Validation |
|---------|---------------------|---------------------|
| **Method** | Rule-based parsing | AI-powered analysis |
| **Speed** | Fast | Slower (API calls) |
| **Cost** | Free | Requires API credits |
| **Accuracy** | Good for common cases | Better for complex scenarios |
| **Context** | SQL structure only | SQL + schema context |

## 🔧 Requirements

- Python 3.8+
- Node.js 16+ (for frontend)
- sqlglot >= 24.0.0
- duckdb >= 0.10.0
- anthropic >= 0.34.0 (optional, for Claude)
- openai >= 1.40.0 (optional, for GPT-4)
- rich >= 13.7.0
- typer >= 0.12.0
- fastapi >= 0.104.0 (for backend)
- langchain >= 0.1.0 (optional, for LangChain validation)
- langchain-openai >= 0.0.5 (optional, for OpenAI integration)
- langchain-anthropic >= 0.1.0 (optional, for Anthropic integration)
- React 18+ (for frontend)

## 📝 Examples

See the `examples/` directory for:
- `example_queries.sql` - Sample SQL statements for testing
- `example_usage.py` - Python API usage examples

## 🧪 Testing

```bash
# Run basic tests
python test_basic.py
```

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Detailed setup and usage
- [Frontend Documentation](README_FRONTEND.md) - Web interface setup
- [LangChain Integration](LANGCHAIN_INTEGRATION.md) - Detailed LangChain implementation guide

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [sqlglot](https://github.com/tobymao/sqlglot) for SQL parsing
- [DuckDB](https://duckdb.org/) for in-memory SQL simulation
- [LangChain](https://www.langchain.com/) for AI orchestration and LCEL chains
- [Anthropic](https://www.anthropic.com/) and [OpenAI](https://openai.com/) for LLM capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the backend API
- [React](https://react.dev/) and [Vite](https://vite.dev/) for the frontend

---

**⚠️ Disclaimer**: SafeSheet is a safety analysis tool and does not execute SQL. Always review generated rollback scripts and test them in a development environment before using in production.
