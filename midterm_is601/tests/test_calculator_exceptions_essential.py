########################
# Essential Calculator Exception Tests #
########################

import pytest
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch, Mock, PropertyMock

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
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


class TestEssentialCalculatorExceptions:
    """Essential exception tests for calculator functionality."""
    
    def test_operation_error_no_operation_set(self, calculator):
        """Test OperationError when no operation is set."""
        with pytest.raises(OperationError, match="No operation set"):
            calculator.perform_operation(2, 3)
    
    def test_validation_error_invalid_input(self, calculator):
        """Test ValidationError with various invalid inputs."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        # Test invalid string
        with pytest.raises(ValidationError, match="Invalid number format"):
            calculator.perform_operation("not_a_number", 3)
        
        # Test empty string  
        with pytest.raises(ValidationError):
            calculator.perform_operation("", 3)
    
    def test_validation_error_exceeds_max_value(self, calculator):
        """Test ValidationError when input exceeds maximum allowed value."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        calculator.config.max_input_value = Decimal('100')
        
        with pytest.raises(ValidationError, match="Value exceeds maximum allowed"):
            calculator.perform_operation(999999, 3)
    
    def test_operation_error_during_calculation(self, calculator):
        """Test OperationError during calculation execution."""
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
        
        with patch('app.calculator.pd.DataFrame.to_csv') as mock_to_csv:
            mock_to_csv.side_effect = Exception("File write error")
            
            with pytest.raises(OperationError, match="Failed to save history: File write error"):
                calculator.save_history()
    
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
                
                with patch('app.calculator.Calculator.load_history') as mock_load_history:
                    mock_load_history.side_effect = Exception("History file corrupted")
                    
                    with patch('app.calculator.logging.warning') as mock_warning:
                        calculator = Calculator(config=config)
                        
                        mock_warning.assert_called_once_with("Could not load existing history: History file corrupted")
                        assert isinstance(calculator, Calculator)
                        assert calculator.history == []
    
    def test_operation_error_with_chained_exception(self, calculator):
        """Test OperationError with chained exceptions from validation."""
        calculator.set_operation(OperationFactory.create_operation('add'))
        
        with patch('app.input_validators.Decimal') as mock_decimal:
            from decimal import InvalidOperation
            mock_decimal.side_effect = InvalidOperation("Invalid decimal")
            
            with pytest.raises(ValidationError, match="Invalid number format"):
                calculator.perform_operation("123.456", 3)
    
    def test_exception_with_observer_notification(self, calculator):
        """Test that exceptions don't break observer functionality."""
        from app.history import LoggingObserver
        
        observer = LoggingObserver()
        calculator.add_observer(observer)
        
        with pytest.raises(OperationError):
            calculator.perform_operation(2, 3)
        
        assert observer in calculator.observers
    
    def test_observer_removal_nonexistent(self, calculator):
        """Test removing a non-existent observer raises ValueError."""
        from app.history import LoggingObserver
        
        observer = LoggingObserver()
        
        with pytest.raises(ValueError):
            calculator.remove_observer(observer)
    
    def test_history_size_limit_enforcement(self, calculator):
        """Test that history does not exceed max size (covers line 219)."""
        calculator.config.max_history_size = 2
        
        add_operation = OperationFactory.create_operation('add')
        calculator.set_operation(add_operation)
        
        # Fill to capacity
        calculator.perform_operation(1, 2)
        calculator.perform_operation(2, 3)
        assert len(calculator.history) == 2
        
        # Exceed capacity - should trigger history.pop(0) on line 219
        calculator.perform_operation(3, 4)
        assert len(calculator.history) == 2
        assert calculator.history[0].operand1 == Decimal('2')  # First was removed
        assert calculator.history[1].operand1 == Decimal('3')  # New one added


class TestInputValidationExceptions:
    """Test input validation edge cases."""
    
    def test_validation_error_boundary_cases(self):
        """Test validation error boundary cases."""
        from app.input_validators import InputValidator
        from app.calculator_config import CalculatorConfig
        
        config = CalculatorConfig()
        
        # Key boundary cases that matter for business logic
        boundary_cases = [
            None,           # Null input
            complex(1, 2),  # Complex numbers (common user mistake)
            float('inf'),   # Infinity (mathematical edge case)
            float('nan'),   # NaN (mathematical edge case)
        ]
        
        for invalid_input in boundary_cases:
            with pytest.raises(ValidationError):
                InputValidator.validate_number(invalid_input, config)


class TestCalculatorSetupExceptions:
    """Test calculator setup and initialization exception paths for 100% coverage."""
    
    def test_logging_setup_failure_lines_103_106(self):
        """Test exception handling in _setup_logging method (lines 103-106)."""
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
                
                # Mock logging.basicConfig to raise an exception (lines 103-106)
                with patch('app.calculator.logging.basicConfig') as mock_basic_config:
                    mock_basic_config.side_effect = Exception("Logging setup failed")
                    
                    # Should print error message and re-raise exception
                    with pytest.raises(Exception, match="Logging setup failed"):
                        Calculator(config=config)
    
    def test_load_history_failure_lines_309_312(self):
        """Test exception handling in load_history method (lines 309-312)."""
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
                
                calculator = Calculator(config=config)
                
                # Mock pandas read_csv to raise an exception (lines 309-312)
                with patch('app.calculator.pd.read_csv') as mock_read_csv:
                    mock_read_csv.side_effect = Exception("File read error")
                    
                    with patch('app.calculator.Path.exists', return_value=True):
                        # Should log error and raise OperationError
                        with pytest.raises(OperationError, match="Failed to load history: File read error"):
                            calculator.load_history()