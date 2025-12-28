"""
SafeSheet - A safety-first SQL tool for preventing accidental data loss.
"""

__version__ = "0.1.0"

from safesheet.safety_report import SafetyReport, analyze_sql
from safesheet.parser import SQLParser
from safesheet.risk_assessor import RiskAssessor
from safesheet.rollback_generator import RollbackGenerator
from safesheet.dry_run import DryRunEngine

__all__ = [
    "SafetyReport",
    "analyze_sql",
    "SQLParser",
    "RiskAssessor",
    "RollbackGenerator",
    "DryRunEngine",
]

