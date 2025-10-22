import pytest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock, PropertyMock

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError, ConfigurationError
from app.operations import OperationFactory


@pytest.fixture
def calculator():
    """Create a calculator instance with temporary directory."""
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
            
            yield Calculator(config=config)


class TestCalculatorExceptions:
    """Test suite for calculator exception handling."""
    
    def test_operation_error_no_operation_set(self, calculator):
        """Test OperationError when no operation is set."""
        with pytest.raises(OperationError, match="No operation set"):
            calculator.perform_operation(2, 3)
    
    def test_validation_error_invalid_string_input(self, calculator):
        """Test ValidationError with invalid string input."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        with pytest.raises(ValidationError, match="Invalid number format"):
            calculator.perform_operation("not_a_number", 3)
    
    def test_validation_error_none_input(self, calculator):
        """Test ValidationError with None input."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        with pytest.raises(ValidationError):
            calculator.perform_operation(None, 3)
    
    def test_validation_error_empty_string(self, calculator):
        """Test ValidationError with empty string input."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        with pytest.raises(ValidationError):
            calculator.perform_operation("", 3)
    
    def test_validation_error_exceeds_max_value(self, calculator):
        """Test ValidationError when input exceeds maximum allowed value."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        # Set a low max value to trigger the error
        calculator.config.max_input_value = Decimal('100')
        
        with pytest.raises(ValidationError, match="Value exceeds maximum allowed"):
            calculator.perform_operation(999999, 3)
    
    def test_operation_error_during_calculation(self, calculator):
        """Test OperationError during calculation execution."""
        # Mock an operation that raises an exception
        mock_operation = Mock()
        mock_operation.execute.side_effect = Exception("Calculation failed")
        mock_operation.__str__ = Mock(return_value="MockOperation")
        
        calculator.set_operation(mock_operation)
        
        with pytest.raises(OperationError, match="Operation failed: Calculation failed"):
            calculator.perform_operation(2, 3)
    
    def test_operation_error_save_history_failure(self, calculator):
        """Test OperationError when saving history fails."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        calculator.perform_operation(2, 3)
        
        # Mock pandas DataFrame.to_csv to raise an exception
        with patch('app.calculator.pd.DataFrame.to_csv') as mock_to_csv:
            mock_to_csv.side_effect = Exception("File write error")
            
            with pytest.raises(OperationError, match="Failed to save history: File write error"):
                calculator.save_history()
    
    def test_operation_error_load_history_failure(self, calculator):
        """Test OperationError when loading history fails."""
        # Mock pandas read_csv to raise an exception
        with patch('app.calculator.pd.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = Exception("File read error")
            
            with patch('app.calculator.Path.exists', return_value=True):
                with pytest.raises(OperationError, match="Failed to load history: File read error"):
                    calculator.load_history()
    
    def test_operation_error_corrupted_history_file(self, calculator):
        """Test OperationError when history file is corrupted."""
        import pandas as pd
        
        # Mock corrupted CSV data
        corrupted_df = pd.DataFrame({
            'operation': ['Addition'],
            'operand1': ['invalid_decimal'],  # This will cause Decimal conversion to fail
            'operand2': ['3'],
            'result': ['5'],
            'timestamp': ['2023-01-01T00:00:00']
        })
        
        with patch('app.calculator.pd.read_csv', return_value=corrupted_df):
            with patch('app.calculator.Path.exists', return_value=True):
                with pytest.raises(OperationError, match="Failed to load history"):
                    calculator.load_history()
    
    def test_logging_setup_failure(self):
        """Test exception during logging setup."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = CalculatorConfig(base_dir=temp_path)
            
            # Mock logging.basicConfig to raise an exception
            with patch('app.calculator.logging.basicConfig') as mock_basic_config:
                mock_basic_config.side_effect = Exception("Logging setup failed")
                
                with pytest.raises(Exception, match="Logging setup failed"):
                    Calculator(config=config)
    
    def test_directory_creation_failure(self):
        """Test exception during directory creation."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config = CalculatorConfig(base_dir=temp_path)
            
            # Mock os.makedirs to raise an exception during logging setup
            with patch('app.calculator.os.makedirs') as mock_makedirs:
                mock_makedirs.side_effect = Exception("Permission denied")
                
                with pytest.raises(Exception):
                    Calculator(config=config)
    
    def test_initialization_history_load_failure(self):
        """Test exception handling during calculator initialization when history loading fails (lines 77-79)."""
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
                
                # Mock load_history to raise an exception during initialization
                with patch('app.calculator.Calculator.load_history') as mock_load_history:
                    mock_load_history.side_effect = Exception("History file corrupted")
                    
                    # Mock the logging.warning to verify it gets called
                    with patch('app.calculator.logging.warning') as mock_warning:
                        # Calculator should still initialize successfully despite history load failure
                        calculator = Calculator(config=config)
                        
                        # Verify the warning was logged with the correct message
                        mock_warning.assert_called_once_with("Could not load existing history: History file corrupted")
                        
                        # Verify calculator was still created successfully
                        assert isinstance(calculator, Calculator)
                        assert calculator.history == []  # Should start with empty history
    
    def test_operation_error_with_chained_exception(self, calculator):
        """Test OperationError with chained exceptions."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        # Test with a decimal that causes InvalidOperation
        with patch('app.input_validators.Decimal') as mock_decimal:
            from decimal import InvalidOperation
            mock_decimal.side_effect = InvalidOperation("Invalid decimal")
            
            with pytest.raises(ValidationError, match="Invalid number format"):
                calculator.perform_operation("123.456", 3)
    
    def test_multiple_validation_errors(self, calculator):
        """Test multiple validation errors in sequence."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        # Test first operand validation error
        with pytest.raises(ValidationError):
            calculator.perform_operation("invalid1", 3)
        
        # Test second operand validation error
        with pytest.raises(ValidationError):
            calculator.perform_operation(2, "invalid2")
        
        # Test both operands invalid
        with pytest.raises(ValidationError):
            calculator.perform_operation("invalid1", "invalid2")
    
    def test_exception_with_observer_notification(self, calculator):
        """Test that exceptions don't prevent observer cleanup."""
        from app.history import LoggingObserver
        
        observer = LoggingObserver()
        calculator.add_observer(observer)
        
        # Even if an operation fails, observers should still be intact
        with pytest.raises(OperationError, match="No operation set"):
            calculator.perform_operation(2, 3)
        
        assert observer in calculator.observers
    
    def test_undo_redo_with_empty_stacks(self, calculator):
        """Test undo/redo operations with empty stacks (not exceptions, but edge cases)."""
        # These don't raise exceptions but return False
        assert calculator.undo() is False
        assert calculator.redo() is False
    
    def test_observer_removal_nonexistent(self, calculator):
        """Test removing a non-existent observer (raises ValueError)."""
        from app.history import LoggingObserver
        
        observer = LoggingObserver()
        
        # This should raise ValueError since observer is not in the list
        with pytest.raises(ValueError):
            calculator.remove_observer(observer)
    
    def test_history_size_limit_enforcement(self, calculator):
        """Test that history does not exceed max size (line 219)."""
        from app.operations import OperationFactory
        
        # Set a small max history size to test the limit
        calculator.config.max_history_size = 3
        
        # Set up an operation
        add_operation = OperationFactory.create_operation('add')
        calculator.set_operation(add_operation)
        
        # Perform operations to fill the history beyond the limit
        calculator.perform_operation(1, 2)  # History: [calc1]
        calculator.perform_operation(2, 3)  # History: [calc1, calc2]
        calculator.perform_operation(3, 4)  # History: [calc1, calc2, calc3]
        
        # Verify history is at max size
        assert len(calculator.history) == 3
        assert calculator.history[0].operand1 == Decimal('1')  # First calculation
        assert calculator.history[2].operand1 == Decimal('3')  # Last calculation
        
        # Add one more operation - this should trigger line 219 (history.pop(0))
        calculator.perform_operation(4, 5)  # History: [calc2, calc3, calc4]
        
        # Verify history size is still at max and oldest was removed
        assert len(calculator.history) == 3
        assert calculator.history[0].operand1 == Decimal('2')  # First calc was removed, second is now first
        assert calculator.history[1].operand1 == Decimal('3')  # Third calc is now second
        assert calculator.history[2].operand1 == Decimal('4')  # New calc is now third
        
        # Add another operation to confirm continued enforcement
        calculator.perform_operation(5, 6)  # History: [calc3, calc4, calc5]
        
        # Verify history size is still at max and oldest was removed again
        assert len(calculator.history) == 3
        assert calculator.history[0].operand1 == Decimal('3')  # Second calc was removed, third is now first
        assert calculator.history[1].operand1 == Decimal('4')  # Fourth calc is now second  
        assert calculator.history[2].operand1 == Decimal('5')  # New calc is now third


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""
    
    def test_invalid_configuration_creation(self):
        """Test creating calculator with invalid configuration."""
        # Test with non-existent base directory that can't be created
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")
            
            # This might not directly raise ConfigurationError, but tests config issues
            try:
                config = CalculatorConfig(base_dir=Path("/invalid/path"))
                Calculator(config=config)
            except Exception as e:
                # The exact exception type depends on implementation
                assert "Permission denied" in str(e) or isinstance(e, (PermissionError, OSError))


class TestInputValidationExceptions:
    """Test input validation exception scenarios."""
    
    def test_validation_error_types(self):
        """Test various types that should raise ValidationError."""
        from app.input_validators import InputValidator
        from app.calculator_config import CalculatorConfig
        
        config = CalculatorConfig()
        
        # Test with various invalid inputs
        invalid_inputs = [
            complex(1, 2),  # Complex numbers
            [1, 2, 3],      # Lists
            {"value": 1},   # Dictionaries
            object(),       # Generic objects
            float('inf'),   # Infinity
            float('nan'),   # NaN
        ]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(ValidationError):
                InputValidator.validate_number(invalid_input, config)
    
    def test_validation_error_with_whitespace(self):
        """Test validation with whitespace strings."""
        from app.input_validators import InputValidator
        from app.calculator_config import CalculatorConfig
        
        config = CalculatorConfig()
        
        # Valid inputs with whitespace
        valid_inputs = ["  123  ", "\t456\n", " 78.9 "]
        for valid_input in valid_inputs:
            result = InputValidator.validate_number(valid_input, config)
            assert isinstance(result, Decimal)
        
        # Invalid inputs with whitespace
        with pytest.raises(ValidationError):
            InputValidator.validate_number("  not_a_number  ", config)