"""Dry-run engine using DuckDB to simulate SQL changes."""

from typing import Dict, Optional
import duckdb
from safesheet.parser import SQLParser


class DryRunEngine:
    """Simulate SQL execution using in-memory DuckDB."""

    def __init__(self, parser: SQLParser):
        """Initialize dry-run engine with a SQL parser."""
        self.parser = parser
        self.conn = None

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection."""
        if self.conn is None:
            self.conn = duckdb.connect(":memory:")
        return self.conn

    def simulate(self, sql: str, sample_data: Optional[Dict[str, list]] = None) -> Dict:
        """Simulate SQL execution and return impact analysis."""
        conn = self._get_connection()
        
        # Create sample tables if provided
        if sample_data:
            for table_name, rows in sample_data.items():
                if rows:
                    # Create table from sample data
                    conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM (VALUES {self._format_rows(rows)})")
        
        impact_radius = self.parser.get_impact_radius()
        statement_type = impact_radius["statement_type"]
        affected_tables = impact_radius["affected_tables"]
        
        result = {
            "simulation_successful": False,
            "statement_type": statement_type,
            "affected_tables": affected_tables,
            "estimated_rows_affected": None,
            "error": None,
            "preview": None,
        }
        
        try:
            if statement_type == "SELECT":
                # For SELECT, just execute and get preview
                query_result = conn.execute(sql).fetchall()
                result["simulation_successful"] = True
                result["preview"] = query_result[:10]  # First 10 rows
                result["estimated_rows_affected"] = len(query_result)
            
            elif statement_type == "UPDATE":
                # For UPDATE, count affected rows before executing
                if affected_tables:
                    table_name = affected_tables[0]
                    # Try to get row count (may fail if table doesn't exist)
                    try:
                        count_before = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                    except:
                        count_before = 0
                    
                    # Execute the update
                    conn.execute(sql)
                    
                    result["simulation_successful"] = True
                    result["estimated_rows_affected"] = "Unknown (table may not exist in simulation)"
                    
                    # Try to get a preview of updated rows
                    try:
                        preview = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
                        result["preview"] = preview
                    except:
                        pass
            
            elif statement_type == "DELETE":
                # Similar to UPDATE
                if affected_tables:
                    table_name = affected_tables[0]
                    try:
                        count_before = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        conn.execute(sql)
                        count_after = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        result["estimated_rows_affected"] = count_before - count_after
                        result["simulation_successful"] = True
                    except Exception as e:
                        result["error"] = f"Could not simulate DELETE: {str(e)}"
                        result["simulation_successful"] = False
            
            elif statement_type == "INSERT":
                # For INSERT, execute and count
                conn.execute(sql)
                if affected_tables:
                    table_name = affected_tables[0]
                    try:
                        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        result["estimated_rows_affected"] = "Unknown (may be 1 or more)"
                        result["simulation_successful"] = True
                    except:
                        result["simulation_successful"] = True
            
            else:
                # For DDL statements (CREATE, ALTER, DROP, TRUNCATE), we can't fully simulate
                result["simulation_successful"] = False
                result["error"] = f"Dry-run simulation not fully supported for {statement_type} statements. These require actual database connection."
        
        except Exception as e:
            result["error"] = str(e)
            result["simulation_successful"] = False
        
        return result

    def _format_rows(self, rows: list) -> str:
        """Format rows for DuckDB VALUES clause."""
        if not rows:
            return ""
        
        # Simple formatting - assumes rows are lists/tuples of values
        formatted = []
        for row in rows:
            if isinstance(row, (list, tuple)):
                values = ", ".join([self._format_value(v) for v in row])
                formatted.append(f"({values})")
        
        return ", ".join(formatted)

    def _format_value(self, value) -> str:
        """Format a single value for SQL."""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value.replace(chr(39), chr(39)+chr(39))}'"  # Escape single quotes
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return f"'{str(value)}'"

    def close(self):
        """Close the DuckDB connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

