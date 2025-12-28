"""Risk assessment engine for SQL statements."""

from typing import Dict, List
from safesheet.parser import SQLParser


class RiskLevel:
    """Risk level constants."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class RiskAssessor:
    """Assess risk level of SQL statements."""

    HIGH_RISK_STATEMENTS = {"ALTER", "DROP", "TRUNCATE"}
    MEDIUM_RISK_STATEMENTS = {"UPDATE", "DELETE"}
    LOW_RISK_STATEMENTS = {"SELECT", "INSERT"}

    def __init__(self, parser: SQLParser):
        """Initialize risk assessor with a SQL parser."""
        self.parser = parser

    def assess_risk(self) -> Dict:
        """Assess the risk level and provide detailed explanation."""
        statement_type = self.parser.get_statement_type()
        impact_radius = self.parser.get_impact_radius()
        
        risk_level = self._determine_risk_level(statement_type)
        warnings = self._generate_warnings(statement_type, impact_radius)
        
        return {
            "risk_level": risk_level,
            "statement_type": statement_type,
            "warnings": warnings,
            "explanation": self._generate_explanation(risk_level, statement_type, impact_radius),
        }

    def _determine_risk_level(self, statement_type: str) -> str:
        """Determine risk level based on statement type."""
        if statement_type in self.HIGH_RISK_STATEMENTS:
            return RiskLevel.HIGH
        elif statement_type in self.MEDIUM_RISK_STATEMENTS:
            return RiskLevel.MEDIUM
        elif statement_type in self.LOW_RISK_STATEMENTS:
            return RiskLevel.LOW
        else:
            return RiskLevel.MEDIUM  # Unknown statements default to medium

    def _generate_warnings(self, statement_type: str, impact_radius: Dict) -> List[str]:
        """Generate specific warnings based on the SQL statement."""
        warnings = []
        
        # High-risk statement warnings
        if statement_type in self.HIGH_RISK_STATEMENTS:
            if statement_type == "ALTER":
                warnings.append(
                    "⚠️  HIGH RISK: ALTER statements modify table structure and cannot be easily undone."
                )
            elif statement_type == "DROP":
                warnings.append(
                    "⚠️  HIGH RISK: DROP statements permanently delete database objects (tables, columns, etc.)."
                )
            elif statement_type == "TRUNCATE":
                warnings.append(
                    "⚠️  HIGH RISK: TRUNCATE permanently deletes all rows from a table without logging individual row deletions."
                )
        
        # Missing WHERE clause warnings
        if statement_type in ("UPDATE", "DELETE") and not impact_radius.get("has_where_clause"):
            affected_tables = impact_radius.get("affected_tables", [])
            warnings.append(
                f"⚠️  CRITICAL: This {statement_type} statement lacks a WHERE clause and will affect ALL rows in {', '.join(affected_tables) if affected_tables else 'target table(s)'}."
            )
        
        # Multiple table warnings
        affected_tables = impact_radius.get("affected_tables", [])
        if len(affected_tables) > 3:
            warnings.append(
                f"⚠️  WARNING: This statement affects {len(affected_tables)} tables, increasing the risk of unintended side effects."
            )
        
        return warnings

    def _generate_explanation(
        self, risk_level: str, statement_type: str, impact_radius: Dict
    ) -> str:
        """Generate a detailed explanation of why this risk level was assigned."""
        affected_tables = impact_radius.get("affected_tables", [])
        has_where = impact_radius.get("has_where_clause", False)
        
        explanation_parts = [f"Risk Level: {risk_level}"]
        
        if risk_level == RiskLevel.HIGH:
            explanation_parts.append(
                f"This is a {statement_type} statement, which is classified as HIGH RISK because it "
                f"permanently modifies database structure or deletes data without row-level logging."
            )
        elif risk_level == RiskLevel.MEDIUM:
            if statement_type in ("UPDATE", "DELETE"):
                if not has_where:
                    explanation_parts.append(
                        f"This {statement_type} statement will affect ALL rows in {', '.join(affected_tables) if affected_tables else 'the target table'} "
                        f"because it lacks a WHERE clause."
                    )
                else:
                    explanation_parts.append(
                        f"This {statement_type} statement will modify data in {', '.join(affected_tables) if affected_tables else 'the target table'}."
                    )
        elif risk_level == RiskLevel.LOW:
            if statement_type == "SELECT":
                explanation_parts.append(
                    "This is a SELECT statement (read-only), which poses minimal risk."
                )
            elif statement_type == "INSERT":
                explanation_parts.append(
                    f"This INSERT statement will add new rows to {', '.join(affected_tables) if affected_tables else 'the target table'}."
                )
        
        return " ".join(explanation_parts)

