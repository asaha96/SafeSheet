"""LLM-powered rollback script generator."""

from typing import Optional
from safesheet.config import Config
from safesheet.parser import SQLParser


class RollbackGenerator:
    """Generate inverse SQL (rollback scripts) using LLM."""

    def __init__(self, parser: SQLParser):
        """Initialize rollback generator with a SQL parser."""
        self.parser = parser
        try:
            self.provider = Config.get_llm_provider()
        except ValueError:
            self.provider = None

    def generate_rollback(self, original_sql: str) -> str:
        """Generate rollback SQL script using LLM."""
        if self.provider is None:
            raise ValueError(
                "No LLM API key configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file"
            )
        elif self.provider == "anthropic":
            return self._generate_with_anthropic(original_sql)
        elif self.provider == "openai":
            return self._generate_with_openai(original_sql)
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def _generate_with_anthropic(self, original_sql: str) -> str:
        """Generate rollback using Anthropic Claude."""
        try:
            from anthropic import Anthropic, APIError
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

        client = Anthropic(api_key=Config.get_anthropic_api_key())
        
        prompt = self._build_prompt(original_sql)
        
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2048,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            rollback_sql = message.content[0].text.strip()
        except APIError as e:
            # Handle specific Anthropic API errors
            if e.status_code == 429:
                raise ValueError(
                    f"Anthropic API quota exceeded. Please check your billing at https://console.anthropic.com/. "
                    f"Error: {str(e)}"
                )
            elif e.status_code == 401:
                raise ValueError("Invalid Anthropic API key. Please check your API key in .env file.")
            else:
                raise ValueError(f"Anthropic API error: {str(e)}")
        
        # Extract SQL from code blocks if present
        if "```" in rollback_sql:
            lines = rollback_sql.split("\n")
            sql_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    sql_lines.append(line)
            rollback_sql = "\n".join(sql_lines).strip()
        
        return rollback_sql

    def _generate_with_openai(self, original_sql: str) -> str:
        """Generate rollback using OpenAI GPT-4."""
        try:
            from openai import OpenAI, APIError
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")

        client = OpenAI(api_key=Config.get_openai_api_key())
        
        prompt = self._build_prompt(original_sql)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a SQL expert specializing in generating idempotent rollback scripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            rollback_sql = response.choices[0].message.content.strip()
        except APIError as e:
            # Handle specific OpenAI API errors
            if e.status_code == 429:
                error_msg = e.response.json() if hasattr(e, 'response') else str(e)
                raise ValueError(
                    f"OpenAI API quota exceeded. Please check your billing at https://platform.openai.com/account/billing. "
                    f"Error: {error_msg}"
                )
            elif e.status_code == 401:
                raise ValueError("Invalid OpenAI API key. Please check your API key in .env file.")
            else:
                raise ValueError(f"OpenAI API error: {str(e)}")
        
        # Extract SQL from code blocks if present
        if "```" in rollback_sql:
            lines = rollback_sql.split("\n")
            sql_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    sql_lines.append(line)
            rollback_sql = "\n".join(sql_lines).strip()
        
        return rollback_sql

    def _build_prompt(self, original_sql: str) -> str:
        """Build the prompt for LLM rollback generation."""
        impact_radius = self.parser.get_impact_radius()
        statement_type = impact_radius["statement_type"]
        affected_tables = impact_radius["affected_tables"]
        
        prompt = f"""You are a Senior Database Engineer. Your task is to generate an IDEMPOTENT rollback SQL script that can undo the following SQL statement.

CRITICAL REQUIREMENTS:
1. The rollback script MUST be idempotent (safe to run multiple times without side effects)
2. The rollback script MUST be syntactically correct and executable
3. For UPDATE statements: Generate a script that restores the previous values
4. For DELETE statements: Generate a script that restores deleted rows (if possible, or provide a backup/restore approach)
5. For INSERT statements: Generate a script that removes the inserted rows
6. For ALTER/DROP/TRUNCATE: Provide a script that recreates the object or restores from backup
7. Include clear comments explaining what the rollback does

Original SQL Statement:
```sql
{original_sql}
```

Statement Type: {statement_type}
Affected Tables: {', '.join(affected_tables) if affected_tables else 'Unknown'}

Generate ONLY the rollback SQL script. If the rollback requires data that may not be available (e.g., previous values for UPDATE), include comments explaining the limitations and suggest a backup-first approach.

Return the SQL script in a code block (```sql ... ```)."""

        return prompt

