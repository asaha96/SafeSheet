#!/usr/bin/env python3
"""Test script to verify DeepSeek-V3.2 integration with all SafeSheet features."""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from safesheet import analyze_sql
from backend.langchain_validator import validate_sql_with_langchain


def test_basic_analysis():
    """Test basic SQL analysis with rollback generation."""
    print("=" * 80)
    print("TEST 1: Basic SQL Analysis with DeepSeek Rollback Generation")
    print("=" * 80)
    
    sql = "UPDATE users SET status = 'inactive'"
    print(f"\nAnalyzing: {sql}\n")
    
    try:
        report = analyze_sql(sql, include_rollback=True, include_dry_run=True)
        print(f"✅ Risk Level: {report.get('risk_level', 'Unknown')}")
        print(f"✅ Statement Type: {report.get('statement_type', 'Unknown')}")
        print(f"✅ Warnings: {len(report.get('warnings', []))} warning(s)")
        
        if report.get('rollback_script'):
            print(f"✅ Rollback Script Generated: {len(report['rollback_script'])} characters")
            print(f"\nRollback Preview:\n{report['rollback_script'][:300]}...")
        else:
            print("❌ No rollback script generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_langchain_validation():
    """Test LangChain validation with DeepSeek."""
    print("\n" + "=" * 80)
    print("TEST 2: LangChain Validation with DeepSeek")
    print("=" * 80)
    
    sql = "DELETE FROM orders WHERE created_at < '2020-01-01'"
    print(f"\nValidating: {sql}\n")
    
    try:
        result = await validate_sql_with_langchain(sql)
        
        if result.get('success'):
            print(f"✅ Validation Successful")
            print(f"✅ Risk Level: {result.get('risk_level', 'Unknown')}")
            print(f"✅ Warnings: {len(result.get('warnings', []))} warning(s)")
            
            for warning in result.get('warnings', [])[:3]:
                print(f"   - {warning}")
            
            if result.get('rollback_sql'):
                print(f"✅ Rollback SQL Generated: {len(result['rollback_sql'])} characters")
                print(f"\nRollback Preview:\n{result['rollback_sql'][:300]}...")
            
            if result.get('duckdb_validation'):
                duckdb = result['duckdb_validation']
                print(f"\n✅ DuckDB Validation:")
                print(f"   - Syntax Valid: {duckdb.get('syntax_valid', False)}")
                print(f"   - Dry Run Successful: {duckdb.get('dry_run_successful', False)}")
        else:
            print(f"❌ Validation Failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_different_risk_levels():
    """Test different SQL risk levels."""
    print("\n" + "=" * 80)
    print("TEST 3: Testing Different Risk Levels")
    print("=" * 80)
    
    test_cases = [
        ("SELECT * FROM users", "Low"),
        ("UPDATE users SET status = 'active' WHERE id = 1", "Medium"),
        ("DROP TABLE users", "High"),
    ]
    
    for sql, expected_risk in test_cases:
        print(f"\nTesting: {sql}")
        try:
            report = analyze_sql(sql, include_rollback=True, include_dry_run=False)
            risk = report.get('risk_level', 'Unknown')
            status = "✅" if risk == expected_risk else "⚠️"
            print(f"{status} Risk Level: {risk} (Expected: {expected_risk})")
            
            if report.get('rollback_script'):
                print(f"   ✅ Rollback script generated")
        except Exception as e:
            print(f"   ❌ Error: {e}")


async def main():
    """Run all tests."""
    print("\n" + "🚀 SafeSheet DeepSeek-V3.2 Integration Test Suite" + "\n")
    
    # Test 1: Basic analysis
    test_basic_analysis()
    
    # Test 2: LangChain validation
    await test_langchain_validation()
    
    # Test 3: Different risk levels
    test_different_risk_levels()
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
