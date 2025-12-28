"""Basic test script to verify SafeSheet functionality."""

from safesheet import SQLParser, RiskAssessor, analyze_sql

def test_parser():
    """Test SQL parser."""
    print("Testing SQL Parser...")
    sql = "UPDATE users SET status = 'inactive' WHERE id = 1"
    parser = SQLParser(sql)
    
    assert parser.get_statement_type() == "UPDATE"
    assert "users" in parser.get_affected_tables()
    assert parser.has_where_clause() == True
    
    print("✅ Parser tests passed!")

def test_risk_assessor():
    """Test risk assessor."""
    print("\nTesting Risk Assessor...")
    
    # Test HIGH RISK
    sql1 = "DROP TABLE users"
    parser1 = SQLParser(sql1)
    assessor1 = RiskAssessor(parser1)
    risk1 = assessor1.assess_risk()
    assert risk1["risk_level"] == "High"
    print("✅ High-risk detection works!")
    
    # Test MEDIUM RISK with missing WHERE
    sql2 = "UPDATE users SET status = 'inactive'"
    parser2 = SQLParser(sql2)
    assessor2 = RiskAssessor(parser2)
    risk2 = assessor2.assess_risk()
    assert risk2["risk_level"] == "Medium"
    assert len(risk2["warnings"]) > 0  # Should warn about missing WHERE
    print("✅ Medium-risk detection with warnings works!")
    
    # Test LOW RISK
    sql3 = "SELECT * FROM users"
    parser3 = SQLParser(sql3)
    assessor3 = RiskAssessor(parser3)
    risk3 = assessor3.assess_risk()
    assert risk3["risk_level"] == "Low"
    print("✅ Low-risk detection works!")

def test_safety_report():
    """Test safety report generation."""
    print("\nTesting Safety Report...")
    
    sql = "UPDATE users SET status = 'inactive'"
    report = analyze_sql(sql, include_rollback=False, include_dry_run=False)
    
    assert report["risk_level"] in ["Low", "Medium", "High"]
    assert report["statement_type"] == "UPDATE"
    assert "impact" in report
    assert "warnings" in report
    
    print("✅ Safety report generation works!")
    print(f"   Risk Level: {report['risk_level']}")
    print(f"   Tables Affected: {report['impact']['tables_affected']}")

if __name__ == "__main__":
    try:
        test_parser()
        test_risk_assessor()
        test_safety_report()
        print("\n" + "="*50)
        print("✅ All basic tests passed!")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

