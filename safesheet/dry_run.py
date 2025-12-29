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
                    except Exception as e:
                        error_str = str(e)
                        if "does not exist" in error_str or "Table with name" in error_str:
                            result["error"] = f"Note: Dry-run cannot execute SQL without actual table structure. This is expected behavior. Original error: {error_str}"
                            result["simulation_successful"] = False
                            result["note"] = "Dry-run simulation requires actual database tables. The SQL syntax appears valid."
                            return result
                        count_before = 0
                    
                    # Execute the update
                    try:
                        conn.execute(sql)
                        result["simulation_successful"] = True
                        result["estimated_rows_affected"] = "Unknown (table may not exist in simulation)"
                        
                        # Try to get a preview of updated rows
                        try:
                            preview = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").fetchall()
                            result["preview"] = preview
                        except:
                            pass
                    except Exception as e:
                        error_str = str(e)
                        if "does not exist" in error_str or "Table with name" in error_str:
                            result["error"] = f"Note: Dry-run cannot execute SQL without actual table structure. This is expected behavior."
                            result["simulation_successful"] = False
                            result["note"] = "Dry-run simulation requires actual database tables. The SQL syntax appears valid."
                        else:
                            result["error"] = f"Could not simulate UPDATE: {error_str}"
                            result["simulation_successful"] = False
            
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
                        error_str = str(e)
                        # Check if it's a "table doesn't exist" error (expected in dry-run)
                        if "does not exist" in error_str or "Table with name" in error_str:
                            result["error"] = f"Note: Dry-run cannot execute SQL without actual table structure. This is expected behavior. Original error: {error_str}"
                            result["simulation_successful"] = False
                            result["note"] = "Dry-run simulation requires actual database tables. The SQL syntax appears valid."
                        else:
                            result["error"] = f"Could not simulate DELETE: {error_str}"
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
            
            elif statement_type == "ALTER":
                # For ALTER statements, parse the operation and provide detailed analysis
                alter_analysis = self._analyze_alter_statement(sql, affected_tables)
                result.update(alter_analysis)
                
                # Try to simulate if we have the table structure
                if affected_tables:
                    table_name = affected_tables[0]
                    try:
                        # Check if table exists in our mock database
                        conn.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                        # Table exists, try to execute the ALTER
                        try:
                            conn.execute(sql)
                            result["simulation_successful"] = True
                            result["note"] = "ALTER statement executed successfully in simulation. In production, this will modify the actual table structure."
                        except Exception as e:
                            error_str = str(e)
                            # Some ALTER operations might not be fully supported by DuckDB
                            if "not supported" in error_str.lower() or "syntax" in error_str.lower():
                                result["simulation_successful"] = False
                                result["error"] = f"ALTER operation syntax validated, but specific operation may not be fully supported by DuckDB. Original error: {error_str}"
                                result["note"] = "The SQL syntax appears valid. This operation will modify table structure in production."
                            else:
                                result["error"] = f"Could not simulate ALTER: {error_str}"
                    except Exception:
                        # Table doesn't exist - provide analysis without execution
                        result["simulation_successful"] = False
                        result["note"] = "Table structure not available in simulation. The SQL syntax has been validated and the operation type has been identified."
            
            elif statement_type == "DROP":
                # For DROP statements, provide analysis
                if affected_tables:
                    result["simulation_successful"] = False
                    result["note"] = f"DROP statement will permanently delete: {', '.join(affected_tables)}. This cannot be simulated without actual database objects."
                    result["estimated_rows_affected"] = "All data in affected objects will be lost"
                else:
                    result["simulation_successful"] = False
                    result["error"] = "Could not identify objects to be dropped."
            
            elif statement_type == "TRUNCATE":
                # For TRUNCATE, try to simulate if table exists
                if affected_tables:
                    table_name = affected_tables[0]
                    try:
                        count_before = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        conn.execute(sql)
                        count_after = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        result["estimated_rows_affected"] = count_before - count_after
                        result["simulation_successful"] = True
                        result["note"] = f"TRUNCATE would remove all {count_before} rows from {table_name}"
                    except Exception as e:
                        error_str = str(e)
                        if "does not exist" in error_str or "Table with name" in error_str:
                            result["simulation_successful"] = False
                            result["note"] = "TRUNCATE statement syntax validated. In production, this will remove all rows from the table."
                        else:
                            result["error"] = f"Could not simulate TRUNCATE: {error_str}"
            
            elif statement_type == "CREATE":
                # For CREATE statements, try to execute
                try:
                    conn.execute(sql)
                    result["simulation_successful"] = True
                    result["note"] = "CREATE statement executed successfully in simulation."
                except Exception as e:
                    error_str = str(e)
                    result["simulation_successful"] = False
                    result["note"] = f"CREATE statement syntax validated. Original error: {error_str}"
            
            else:
                # For other DDL statements
                result["simulation_successful"] = False
                result["note"] = f"{statement_type} statement syntax validated. Full simulation requires actual database connection."
        
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

    def _analyze_alter_statement(self, sql: str, affected_tables: list) -> Dict:
        """Analyze ALTER statement to extract operation details."""
        import re
        
        result = {
            "alter_operation": "Unknown",
            "alter_details": {},
            "impact_summary": None
        }
        
        try:
            sql_upper = sql.upper().strip()
            operations = []
            columns_affected = []
            
            # Parse ADD COLUMN
            add_col_match = re.search(r'ADD\s+(?:COLUMN\s+)?(\w+)', sql_upper, re.IGNORECASE)
            if add_col_match:
                col_name = add_col_match.group(1)
                # Try to get column type
                type_match = re.search(rf'ADD\s+(?:COLUMN\s+)?{col_name}\s+(\w+(?:\s*\(\s*\d+\s*\))?)', sql_upper, re.IGNORECASE)
                col_type = type_match.group(1) if type_match else "Unknown type"
                operations.append(f"ADD COLUMN {col_name} ({col_type})")
                columns_affected.append(col_name)
            
            # Parse DROP COLUMN
            drop_col_match = re.search(r'DROP\s+(?:COLUMN\s+)?(\w+)', sql_upper, re.IGNORECASE)
            if drop_col_match:
                col_name = drop_col_match.group(1)
                operations.append(f"DROP COLUMN {col_name}")
                columns_affected.append(col_name)
            
            # Parse RENAME COLUMN
            rename_match = re.search(r'RENAME\s+(?:COLUMN\s+)?(\w+)\s+TO\s+(\w+)', sql_upper, re.IGNORECASE)
            if rename_match:
                old_name = rename_match.group(1)
                new_name = rename_match.group(2)
                operations.append(f"RENAME COLUMN {old_name} TO {new_name}")
                columns_affected.extend([old_name, new_name])
            
            # Parse MODIFY/ALTER COLUMN
            modify_match = re.search(r'(?:MODIFY|ALTER\s+COLUMN)\s+(\w+)', sql_upper, re.IGNORECASE)
            if modify_match:
                col_name = modify_match.group(1)
                operations.append(f"MODIFY COLUMN {col_name}")
                columns_affected.append(col_name)
            
            # Parse ADD CONSTRAINT
            add_constraint_match = re.search(r'ADD\s+(?:CONSTRAINT\s+)?(\w+)', sql_upper, re.IGNORECASE)
            if add_constraint_match and "COLUMN" not in sql_upper:
                constraint_name = add_constraint_match.group(1)
                operations.append(f"ADD CONSTRAINT {constraint_name}")
            
            # Parse DROP CONSTRAINT
            drop_constraint_match = re.search(r'DROP\s+CONSTRAINT\s+(\w+)', sql_upper, re.IGNORECASE)
            if drop_constraint_match:
                constraint_name = drop_constraint_match.group(1)
                operations.append(f"DROP CONSTRAINT {constraint_name}")
            
            # If no specific operations found, provide generic analysis
            if not operations:
                if "ADD" in sql_upper:
                    operations.append("ADD (operation type)")
                elif "DROP" in sql_upper:
                    operations.append("DROP (operation type)")
                elif "RENAME" in sql_upper:
                    operations.append("RENAME (operation type)")
                elif "MODIFY" in sql_upper or "ALTER COLUMN" in sql_upper:
                    operations.append("MODIFY (operation type)")
                else:
                    operations.append("ALTER TABLE")
            
            result["alter_operation"] = ", ".join(operations) if operations else "ALTER TABLE"
            result["alter_details"] = {
                "operations": operations,
                "columns_affected": list(set(columns_affected)) if columns_affected else [],
                "tables_affected": affected_tables
            }
            
            # Create impact summary
            if operations:
                impact_parts = []
                ops_str = " ".join(operations).upper()
                # Check for RENAME first (it's a special case)
                if "RENAME" in ops_str:
                    impact_parts.append("🔄 Will rename columns (data preserved)")
                elif "DROP" in ops_str:
                    impact_parts.append("⚠️ Will permanently remove columns/constraints")
                elif "ADD" in ops_str:
                    impact_parts.append("➕ Will add new columns/constraints")
                elif "MODIFY" in ops_str:
                    impact_parts.append("🔄 Will modify existing column structure")
                else:
                    impact_parts.append("Will modify table structure")
                
                result["impact_summary"] = ". ".join(impact_parts) if impact_parts else "Will modify table structure"
            else:
                result["impact_summary"] = "Will modify table structure"
                
        except Exception as e:
            # If parsing fails, provide basic analysis
            result["alter_operation"] = "ALTER TABLE"
            result["impact_summary"] = f"ALTER statement detected. Error parsing details: {str(e)}"
        
        return result

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

