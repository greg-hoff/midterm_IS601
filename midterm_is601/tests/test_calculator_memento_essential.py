########################
# Essential Calculator Memento Tests #
########################

import pytest
import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, PropertyMock

from app.calculator_memento import CalculatorMemento
from app.calculation import Calculation
from app.exceptions import OperationError


class TestCalculatorMemento:
    """Essential test suite for CalculatorMemento class."""

    @pytest.fixture
    def sample_calculations(self):
        """Create sample calculations for testing."""
        calc1 = Calculation("Addition", Decimal("2"), Decimal("3"))
        calc2 = Calculation("Multiplication", Decimal("4"), Decimal("5"))
        return [calc1, calc2]

    def test_memento_creation_empty_and_with_data(self, sample_calculations):
        """Test creating mementos with empty and populated history."""
        # Empty history
        empty_memento = CalculatorMemento(history=[])
        assert empty_memento.history == []
        assert isinstance(empty_memento.timestamp, datetime.datetime)
        
        # With calculations
        memento = CalculatorMemento(history=sample_calculations)
        assert len(memento.history) == 2
        assert memento.history[0].operation == "Addition"
        assert memento.history[0].result == Decimal("5")

    def test_memento_serialization_to_dict(self, sample_calculations):
        """Test converting memento to dictionary."""
        memento = CalculatorMemento(history=sample_calculations)
        result_dict = memento.to_dict()
        
        assert 'history' in result_dict
        assert 'timestamp' in result_dict
        assert len(result_dict['history']) == 2
        assert result_dict['history'][0]['operation'] == 'Addition'
        assert result_dict['history'][1]['operation'] == 'Multiplication'

    def test_memento_deserialization_from_dict(self):
        """Test creating memento from dictionary."""
        data = {
            'history': [
                {
                    'operation': 'Subtraction',
                    'operand1': '10',
                    'operand2': '3',
                    'result': '7',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            ],
            'timestamp': datetime.datetime(2023, 6, 15, 10, 30, 0).isoformat()
        }
        
        memento = CalculatorMemento.from_dict(data)
        assert len(memento.history) == 1
        assert memento.history[0].operation == 'Subtraction'
        assert memento.history[0].result == Decimal('7')

    def test_memento_roundtrip_integrity(self, sample_calculations):
        """Test that memento preserves data through serialization roundtrip."""
        original_memento = CalculatorMemento(history=sample_calculations)
        
        # Serialize and deserialize
        memento_dict = original_memento.to_dict()
        restored_memento = CalculatorMemento.from_dict(memento_dict)
        
        # Verify data integrity
        assert len(restored_memento.history) == len(original_memento.history)
        assert restored_memento.timestamp == original_memento.timestamp
        
        for original, restored in zip(original_memento.history, restored_memento.history):
            assert original.operation == restored.operation
            assert original.operand1 == restored.operand1
            assert original.operand2 == restored.operand2
            assert original.result == restored.result

    def test_memento_error_handling(self):
        """Test memento handles invalid data appropriately."""
        # Missing required fields
        with pytest.raises((KeyError, ValueError)):
            CalculatorMemento.from_dict({'history': []})  # Missing timestamp
        
        with pytest.raises((KeyError, ValueError)):
            CalculatorMemento.from_dict({'timestamp': datetime.datetime.now().isoformat()})  # Missing history
        
        # Invalid timestamp
        with pytest.raises(ValueError):
            CalculatorMemento.from_dict({
                'history': [],
                'timestamp': 'invalid-timestamp'
            })

    def test_memento_invalid_calculation_propagation(self):
        """Test that calculation errors are properly propagated."""
        data = {
            'history': [
                {
                    'operation': 'Addition',
                    'operand1': 'invalid_decimal',
                    'operand2': '3',
                    'result': '5',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            ],
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        with pytest.raises(OperationError):
            CalculatorMemento.from_dict(data)

    def test_memento_calculator_integration(self):
        """Test memento works with actual calculator instances."""
        from app.calculator import Calculator
        from app.calculator_config import CalculatorConfig
        from app.operations import OperationFactory
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = CalculatorConfig(base_dir=temp_path)
            
            with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
                 patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
                 patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
                 patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
                
                mock_log_dir.return_value = temp_path / "logs"
                mock_log_file.return_value = temp_path / "logs/calculator.log"
                mock_history_dir.return_value = temp_path / "history"
                mock_history_file.return_value = temp_path / "history/calculator_history.csv"
                
                # Create calculator and perform operations
                calculator = Calculator(config=config)
                calculator.set_operation(OperationFactory.create_operation('add'))
                calculator.perform_operation(2, 3)
                calculator.perform_operation(5, 7)
                
                # Create and test memento from real calculator state
                memento = CalculatorMemento(history=calculator.history.copy())
                assert len(memento.history) == 2
                assert memento.history[0].result == Decimal("5")
                assert memento.history[1].result == Decimal("12")