import pytest
from decimal import Decimal
from datetime import datetime
from app.calculation import Calculation
from app.exceptions import OperationError
import logging


def test_addition():
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    assert calc.result == Decimal("5")


def test_subtraction():
    calc = Calculation(operation="Subtraction", operand1=Decimal("5"), operand2=Decimal("3"))
    assert calc.result == Decimal("2")


def test_multiplication():
    calc = Calculation(operation="Multiplication", operand1=Decimal("4"), operand2=Decimal("2"))
    assert calc.result == Decimal("8")


def test_division():
    calc = Calculation(operation="Division", operand1=Decimal("8"), operand2=Decimal("2"))
    assert calc.result == Decimal("4")


def test_division_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation(operation="Division", operand1=Decimal("8"), operand2=Decimal("0"))


def test_power():
    calc = Calculation(operation="Power", operand1=Decimal("2"), operand2=Decimal("3"))
    assert calc.result == Decimal("8")


def test_negative_power():
    with pytest.raises(OperationError, match="Negative exponents are not supported"):
        Calculation(operation="Power", operand1=Decimal("2"), operand2=Decimal("-3"))


def test_root():
    calc = Calculation(operation="Root", operand1=Decimal("16"), operand2=Decimal("2"))
    assert calc.result == Decimal("4")


def test_invalid_root():
    with pytest.raises(OperationError, match="Cannot calculate root of negative number"):
        Calculation(operation="Root", operand1=Decimal("-16"), operand2=Decimal("2"))

# Added test for zero root - Greg H
def test_zero_root():
    """Test that attempting to calculate a root with zero degree raises appropriate error."""
    with pytest.raises(OperationError, match="Zero root is undefined"):
        Calculation(operation="Root", operand1=Decimal("16"), operand2=Decimal("0"))


def test_calculation_error_handling():
    """Test that calculation errors are properly wrapped in OperationError."""
    # Create a calculation that will cause an arithmetic error
    with pytest.raises(OperationError, match="Calculation failed"):
        # This should trigger an OverflowError or similar when trying to compute huge power
        Calculation(operation="Power", operand1=Decimal("10"), operand2=Decimal("10000"))

# Added test for Modulus - Greg H
def test_modulus():
    calc = Calculation(operation="Modulus", operand1=Decimal("10"), operand2=Decimal("3"))
    assert calc.result == Decimal("1")

# Added test for Modulus by zero - Greg H    
def test_modulus_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation(operation="Modulus", operand1=Decimal("10"), operand2=Decimal("0"))

# Added test for IntegerDivision - Greg H
def test_integer_division():
    calc = Calculation(operation="IntegerDivision", operand1=Decimal("10"), operand2=Decimal("3"))
    assert calc.result == Decimal("3")

# Added test for IntegerDivision by zero - Greg H
def test_integer_division_by_zero():
    with pytest.raises(OperationError, match="Division by zero is not allowed"):
        Calculation(operation="IntegerDivision", operand1=Decimal("10"), operand2=Decimal("0"))

# Added test for Percentage - Greg H
def test_percentage():
    calc = Calculation(operation="Percentage", operand1=Decimal("50"), operand2=Decimal("200"))
    assert calc.result == Decimal("25")

# Added test for AbsoluteDifference - Greg H
def test_absolute_difference():
    calc = Calculation(operation="Subtraction", operand1=Decimal("5"), operand2=Decimal("10"))
    assert abs(calc.result) == Decimal("5")

def test_unknown_operation():
    with pytest.raises(OperationError, match="Unknown operation"):
        Calculation(operation="Unknown", operand1=Decimal("5"), operand2=Decimal("3"))


def test_to_dict():
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    result_dict = calc.to_dict()
    assert result_dict == {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": calc.timestamp.isoformat()
    }


def test_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    calc = Calculation.from_dict(data)
    assert calc.operation == "Addition"
    assert calc.operand1 == Decimal("2")
    assert calc.operand2 == Decimal("3")
    assert calc.result == Decimal("5")


def test_invalid_from_dict():
    data = {
        "operation": "Addition",
        "operand1": "invalid",
        "operand2": "3",
        "result": "5",
        "timestamp": datetime.now().isoformat()
    }
    with pytest.raises(OperationError, match="Invalid calculation data"):
        Calculation.from_dict(data)


def test_format_result():
    calc = Calculation(operation="Division", operand1=Decimal("1"), operand2=Decimal("3"))
    assert calc.format_result(precision=2) == "0.33"
    assert calc.format_result(precision=10) == "0.3333333333"


def test_equality():
    calc1 = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    calc2 = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    calc3 = Calculation(operation="Subtraction", operand1=Decimal("5"), operand2=Decimal("3"))
    assert calc1 == calc2
    assert calc1 != calc3

# Added equality test with non-Calculation objects - Greg H
def test_equality_with_non_calculation():
    """Test equality comparison with non-Calculation objects returns NotImplemented."""
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    
    # Test comparison with different types - should return False (not equal)
    assert calc != "not a calculation"
    assert calc != 5
    assert calc != None
    assert calc != {"operation": "Addition"}
    
    # Test that the __eq__ method returns NotImplemented for non-Calculation objects
    result = calc.__eq__("not a calculation")
    assert result is NotImplemented



# New Test to Cover Logging Warning
def test_from_dict_result_mismatch(caplog):
    """
    Test the from_dict method to ensure it logs a warning when the saved result
    does not match the computed result.
    """
    # Arrange
    data = {
        "operation": "Addition",
        "operand1": "2",
        "operand2": "3",
        "result": "10",  # Incorrect result to trigger logging.warning
        "timestamp": datetime.now().isoformat()
    }

    # Act
    with caplog.at_level(logging.WARNING):
        calc = Calculation.from_dict(data)

    # Assert
    assert "Loaded calculation result 10 differs from computed result 5" in caplog.text

# Added tests for string representations - Greg H
def test_str_representation():
    """Test the __str__ method returns correct string representation."""
    calc = Calculation(operation="Addition", operand1=Decimal("2"), operand2=Decimal("3"))
    expected_str = "Addition(2, 3) = 5"
    assert str(calc) == expected_str


def test_repr_representation():
    """Test the __repr__ method returns correct detailed representation."""
    calc = Calculation(operation="Multiplication", operand1=Decimal("4"), operand2=Decimal("5"))
    repr_str = repr(calc)
    assert "Calculation(operation='Multiplication'" in repr_str
    assert "operand1=4" in repr_str
    assert "operand2=5" in repr_str
    assert "result=20" in repr_str
    assert "timestamp=" in repr_str
