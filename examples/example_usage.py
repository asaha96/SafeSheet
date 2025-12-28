"""Example usage of SafeSheet programmatically."""

from safesheet import analyze_sql, SafetyReport

# Example 1: Simple analysis
print("=" * 80)
print("Example 1: Analyzing a dangerous UPDATE statement")
print("=" * 80)

sql = "UPDATE users SET status = 'inactive'"
report = analyze_sql(sql, include_rollback=True, include_dry_run=True)

print(f"Risk Level: {report['risk_level']}")
print(f"Statement Type: {report['statement_type']}")
print(f"Tables Affected: {report['impact']['tables_affected']}")
print(f"\nWarnings:")
for warning in report['warnings']:
    print(f"  {warning}")

print(f"\nRollback Script:")
print(report['rollback_script'])

# Example 2: Using SafetyReport class directly
print("\n" + "=" * 80)
print("Example 2: Using SafetyReport class with formatted output")
print("=" * 80)

sql2 = "DELETE FROM orders WHERE created_at < '2020-01-01'"
report_generator = SafetyReport(sql2, include_rollback=True, include_dry_run=False)
report2 = report_generator.generate()
formatted = report_generator.format_report(report2)
print(formatted)

# Example 3: High-risk statement
print("\n" + "=" * 80)
print("Example 3: High-risk TRUNCATE statement")
print("=" * 80)

sql3 = "TRUNCATE TABLE logs"
report3 = analyze_sql(sql3, include_rollback=True, include_dry_run=False)
print(f"Risk Level: {report3['risk_level']}")
print(f"Explanation: {report3['explanation']}")
print(f"\nWarnings:")
for warning in report3['warnings']:
    print(f"  {warning}")

