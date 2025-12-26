import math
from core import (
    calculate_retirement_deduction,
    calculate_income_tax,
    calculate_pension_deduction,
    adjusted_deduction_with_19_year_rule,
    calculate_public_pension,
)

def test_retirement_deduction_branch():
    assert calculate_retirement_deduction(1) == 80
    assert calculate_retirement_deduction(20) == 800
    assert calculate_retirement_deduction(21) == 870

def test_income_tax_nonnegative():
    assert calculate_income_tax(0) == 0
    assert calculate_income_tax(100) > 0

def test_pension_deduction_boundary():
    assert calculate_pension_deduction(130, 64) == 60
    assert calculate_pension_deduction(330, 65) == 110

def test_19year_rule_adjustment_nonnegative():
    prev = {"age": 60, "periods":[{"startAge":40, "endAge":60}]}
    cur  = {"age": 70, "periods":[{"startAge":50, "endAge":70}]}
    assert adjusted_deduction_with_19_year_rule(cur, prev) >= 0

def test_public_pension_nonnegative():
    assert calculate_public_pension(avg_salary=30, years_of_service=20, exemption=False, retirement_age=60) >= 0
