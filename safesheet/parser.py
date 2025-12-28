"""SQL parsing using sqlglot to identify impact radius."""

from typing import List, Set, Dict, Optional
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


class SQLParser:
    """Parse SQL statements to identify affected tables and columns."""

    def __init__(self, sql: str):
        """Initialize parser with SQL statement."""
        self.sql = sql.strip()
        self.parsed = None
        self._parse()

    def _parse(self) -> None:
        """Parse the SQL statement."""
        try:
            self.parsed = sqlglot.parse_one(self.sql, read=None)
        except ParseError as e:
            raise ValueError(f"Failed to parse SQL: {e}")

    def get_statement_type(self) -> str:
        """Get the type of SQL statement (SELECT, UPDATE, DELETE, etc.)."""
        if not self.parsed:
            return "UNKNOWN"
        
        statement_type = type(self.parsed).__name__.upper()
        # Map to common SQL statement types
        type_mapping = {
            "SELECT": "SELECT",
            "UPDATE": "UPDATE",
            "DELETE": "DELETE",
            "INSERT": "INSERT",
            "CREATE": "CREATE",
            "ALTER": "ALTER",
            "DROP": "DROP",
            "TRUNCATE": "TRUNCATE",
        }
        
        for key, value in type_mapping.items():
            if key in statement_type:
                return value
        
        return statement_type

    def get_affected_tables(self) -> Set[str]:
        """Get set of tables affected by this SQL statement."""
        tables = set()
        
        if not self.parsed:
            return tables

        # Find all table references
        for table in self.parsed.find_all(exp.Table):
            tables.add(table.name)

        return tables

    def get_affected_columns(self) -> Dict[str, Set[str]]:
        """Get dictionary mapping table names to sets of affected columns."""
        columns_by_table: Dict[str, Set[str]] = {}
        
        if not self.parsed:
            return columns_by_table

        statement_type = self.get_statement_type()

        # For UPDATE statements, find columns being set
        if statement_type == "UPDATE":
            # Get the main table from UPDATE statement
            update_expr = self.parsed
            if isinstance(update_expr, exp.Update):
                # Get table name
                table_expr = update_expr.this
                if isinstance(table_expr, exp.Table):
                    table_name = table_expr.name
                else:
                    # Try to get from find_all
                    tables = list(update_expr.find_all(exp.Table))
                    table_name = tables[0].name if tables else "unknown"
                
                if table_name not in columns_by_table:
                    columns_by_table[table_name] = set()
                
                # Find SET expressions - columns being updated
                for set_expr in update_expr.find_all(exp.Set):
                    # The Set expression contains assignments like "column = value"
                    for assignment in set_expr.expressions:
                        if isinstance(assignment, exp.EQ):
                            # Left side is the column
                            if isinstance(assignment.this, exp.Column):
                                columns_by_table[table_name].add(assignment.this.name)
                        elif isinstance(assignment, exp.Column):
                            columns_by_table[table_name].add(assignment.name)

        # For INSERT statements, find columns being inserted
        elif statement_type == "INSERT":
            for insert in self.parsed.find_all(exp.Insert):
                table_name = insert.this.name if hasattr(insert, "this") else "unknown"
                if table_name not in columns_by_table:
                    columns_by_table[table_name] = set()
                
                # Find columns in INSERT
                for column in insert.find_all(exp.Column):
                    columns_by_table[table_name].add(column.name)

        # For DELETE, we don't know specific columns
        elif statement_type == "DELETE":
            tables = self.get_affected_tables()
            for table in tables:
                columns_by_table[table] = set()  # All columns potentially affected

        # For ALTER, DROP, TRUNCATE - all columns potentially affected
        elif statement_type in ("ALTER", "DROP", "TRUNCATE"):
            tables = self.get_affected_tables()
            for table in tables:
                columns_by_table[table] = set()  # All columns potentially affected

        return columns_by_table

    def has_where_clause(self) -> bool:
        """Check if the SQL statement has a WHERE clause."""
        if not self.parsed:
            return False
        
        return bool(self.parsed.find(exp.Where))

    def get_where_clause(self) -> Optional[str]:
        """Get the WHERE clause as a string."""
        if not self.parsed:
            return None
        
        where_expr = self.parsed.find(exp.Where)
        if where_expr:
            return where_expr.sql()
        return None

    def get_impact_radius(self) -> Dict:
        """Get comprehensive impact radius information."""
        return {
            "statement_type": self.get_statement_type(),
            "affected_tables": list(self.get_affected_tables()),
            "affected_columns": {
                table: list(columns)
                for table, columns in self.get_affected_columns().items()
            },
            "has_where_clause": self.has_where_clause(),
            "where_clause": self.get_where_clause(),
        }

