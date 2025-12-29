"""Safety report generator combining all SafeSheet components."""

from typing import Dict, Optional
from safesheet.parser import SQLParser
from safesheet.risk_assessor import RiskAssessor
from safesheet.rollback_generator import RollbackGenerator
from safesheet.dry_run import DryRunEngine


class SafetyReport:
    """Comprehensive safety report for SQL statements."""

    def __init__(
        self,
        sql: str,
        include_rollback: bool = True,
        include_dry_run: bool = True,
        sample_data: Optional[Dict[str, list]] = None,
    ):
        """Initialize safety report generator."""
        self.sql = sql
        self.include_rollback = include_rollback
        self.include_dry_run = include_dry_run
        self.sample_data = sample_data or {}
        
        # Initialize components
        self.parser = SQLParser(sql)
        self.risk_assessor = RiskAssessor(self.parser)
        self.rollback_generator = RollbackGenerator(self.parser) if include_rollback else None
        self.dry_run_engine = DryRunEngine(self.parser) if include_dry_run else None

    def generate(self) -> Dict:
        """Generate comprehensive safety report."""
        # Get impact radius
        impact_radius = self.parser.get_impact_radius()
        
        # Assess risk
        risk_assessment = self.risk_assessor.assess_risk()
        
        # Generate rollback (if requested)
        rollback_script = None
        rollback_error = None
        if self.include_rollback and self.rollback_generator:
            try:
                rollback_script = self.rollback_generator.generate_rollback(self.sql)
            except Exception as e:
                rollback_error = str(e)
                rollback_script = f"-- Error generating rollback: {str(e)}\n-- Manual rollback may be required."
        
        # Run dry-run simulation (if requested)
        dry_run_result = None
        if self.include_dry_run and self.dry_run_engine:
            try:
                dry_run_result = self.dry_run_engine.simulate(self.sql, self.sample_data)
            except Exception as e:
                dry_run_result = {
                    "simulation_successful": False,
                    "error": str(e),
                }
        
        # Calculate impact summary
        affected_tables = impact_radius.get("affected_tables", [])
        affected_columns = impact_radius.get("affected_columns", {})
        
        total_tables = len(affected_tables)
        total_columns = sum(len(cols) for cols in affected_columns.values())
        
        # Build report
        report = {
            "sql": self.sql,
            "risk_level": risk_assessment["risk_level"],
            "statement_type": risk_assessment["statement_type"],
            "impact": {
                "tables_affected": total_tables,
                "tables": affected_tables,
                "columns_affected": total_columns,
                "columns_by_table": affected_columns,
                "has_where_clause": impact_radius.get("has_where_clause", False),
            },
            "warnings": risk_assessment["warnings"],
            "explanation": risk_assessment["explanation"],
            "rollback_script": rollback_script,
            "rollback_error": rollback_error,
            "dry_run": dry_run_result,
        }
        
        return report

    def format_report(self, report: Optional[Dict] = None) -> str:
        """Format safety report as a human-readable string."""
        if report is None:
            report = self.generate()
        
        lines = []
        lines.append("=" * 80)
        lines.append("SAFETY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # SQL Statement
        lines.append("SQL Statement:")
        lines.append("-" * 80)
        lines.append(report["sql"])
        lines.append("")
        
        # Risk Level
        risk_level = report["risk_level"]
        risk_emoji = {"Low": "✅", "Medium": "⚠️", "High": "🚨"}
        lines.append(f"Risk Level: {risk_emoji.get(risk_level, '⚠️')} {risk_level}")
        lines.append("")
        
        # Statement Type
        lines.append(f"Statement Type: {report['statement_type']}")
        lines.append("")
        
        # Impact
        lines.append("Impact Analysis:")
        lines.append("-" * 80)
        impact = report["impact"]
        lines.append(f"  Tables Affected: {impact['tables_affected']}")
        if impact["tables"]:
            lines.append(f"  Tables: {', '.join(impact['tables'])}")
        lines.append(f"  Columns Affected: {impact['columns_affected']}")
        if impact["columns_by_table"]:
            for table, columns in impact["columns_by_table"].items():
                if columns:
                    lines.append(f"    - {table}: {', '.join(columns)}")
                else:
                    lines.append(f"    - {table}: All columns")
        lines.append(f"  Has WHERE Clause: {impact['has_where_clause']}")
        lines.append("")
        
        # Warnings
        if report["warnings"]:
            lines.append("Warnings:")
            lines.append("-" * 80)
            for warning in report["warnings"]:
                lines.append(f"  {warning}")
            lines.append("")
        
        # Explanation
        lines.append("Explanation:")
        lines.append("-" * 80)
        lines.append(f"  {report['explanation']}")
        lines.append("")
        
        # Dry Run Results
        if report.get("dry_run"):
            lines.append("Dry Run Simulation:")
            lines.append("-" * 80)
            dry_run = report["dry_run"]
            if dry_run.get("simulation_successful"):
                lines.append("  ✅ Simulation completed successfully")
                if dry_run.get("estimated_rows_affected") is not None:
                    lines.append(f"  Estimated Rows Affected: {dry_run['estimated_rows_affected']}")
            else:
                # For ALTER and other DDL statements, show analysis instead of just error
                if dry_run.get("alter_operation"):
                    lines.append("  📊 ALTER Statement Analysis:")
                    lines.append(f"  Operation: {dry_run.get('alter_operation', 'Unknown')}")
                    if dry_run.get("impact_summary"):
                        lines.append(f"  Impact: {dry_run['impact_summary']}")
                    if dry_run.get("alter_details", {}).get("columns_affected"):
                        cols = dry_run["alter_details"]["columns_affected"]
                        if cols:
                            lines.append(f"  Columns Affected: {', '.join(cols)}")
                    if dry_run.get("note"):
                        lines.append(f"  ℹ️  {dry_run['note']}")
                elif dry_run.get("note"):
                    lines.append(f"  ℹ️  {dry_run['note']}")
                else:
                    lines.append("  ⚠️  Simulation had issues")
                    if dry_run.get("error"):
                        lines.append(f"  Error: {dry_run['error']}")
            lines.append("")
        
        # Rollback Script
        if report.get("rollback_script"):
            lines.append("Rollback Script:")
            lines.append("-" * 80)
            if report.get("rollback_error"):
                lines.append(f"  ⚠️  {report['rollback_error']}")
                lines.append("")
            lines.append(report["rollback_script"])
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)


def analyze_sql(
    sql: str,
    include_rollback: bool = True,
    include_dry_run: bool = True,
    sample_data: Optional[Dict[str, list]] = None,
) -> Dict:
    """Convenience function to analyze SQL and return safety report."""
    report_generator = SafetyReport(
        sql=sql,
        include_rollback=include_rollback,
        include_dry_run=include_dry_run,
        sample_data=sample_data,
    )
    return report_generator.generate()

