import datetime
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from tempfile import TemporaryDirectory
from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver, AutoSaveObserver
from app.operations import OperationFactory

# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

        # Patch properties to use the temporary directory paths
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
            
            # Set return values to use paths within the temporary directory
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"
            
            # Return an instance of Calculator with the mocked config
            yield Calculator(config=config)

# Test Calculator Initialization

def test_calculator_initialization(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None

# Test Logging Setup

@patch('app.calculator.logging.info')
def test_logging_setup(logging_info_mock):
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        
        # Instantiate calculator to trigger logging
        calculator = Calculator(CalculatorConfig())
        logging_info_mock.assert_any_call("Calculator initialized with configuration")

# Test Adding and Removing Observers

def test_add_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    assert observer in calculator.observers

def test_remove_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers

# Test Setting Operations

def test_set_operation(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation

# Test Performing Operations

def test_perform_operation_addition(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    result = calculator.perform_operation(2, 3)
    assert result == Decimal('5')

def test_perform_operation_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)

def test_perform_operation_operation_error(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)

# Test Undo/Redo Functionality

def test_undo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.history == []

def test_redo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    calculator.redo()
    assert len(calculator.history) == 1

# Test History Management

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()

@patch('app.calculator.pd.read_csv')
@patch('app.calculator.Path.exists', return_value=True)
def test_load_history(mock_exists, mock_read_csv, calculator):
    # Mock CSV data to match the expected format in from_dict
    mock_read_csv.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })
    
    # Test the load_history functionality
    try:
        calculator.load_history()
        # Verify history length after loading
        assert len(calculator.history) == 1
        # Verify the loaded values
        assert calculator.history[0].operation == "Addition"
        assert calculator.history[0].operand1 == Decimal("2")
        assert calculator.history[0].operand2 == Decimal("3")
        assert calculator.history[0].result == Decimal("5")
    except OperationError:
        pytest.fail("Loading history failed due to OperationError")
        
            
# Test Clearing History

def test_clear_history(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.clear_history()
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

# Test DataFrame History
# Added by Greg Hoffer - with help of Claude

def test_get_history_dataframe_empty(calculator):
    """Test get_history_dataframe with empty history."""
    df = calculator.get_history_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 0
    # Empty DataFrame may not have columns, but when it does have data, 
    # it should have the expected columns

def test_get_history_dataframe_with_calculations(calculator):
    """Test get_history_dataframe with calculations in history."""
    # Add some calculations to history
    add_operation = OperationFactory.create_operation('add')
    calculator.set_operation(add_operation)
    calculator.perform_operation(2, 3)
    
    multiply_operation = OperationFactory.create_operation('multiply')
    calculator.set_operation(multiply_operation)
    calculator.perform_operation(4, 5)
    
    # Get DataFrame
    df = calculator.get_history_dataframe()
    
    # Verify DataFrame structure and content
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['operation', 'operand1', 'operand2', 'result', 'timestamp']
    
    # Check first calculation
    assert df.iloc[0]['operation'] == 'Addition'
    assert df.iloc[0]['operand1'] == '2'
    assert df.iloc[0]['operand2'] == '3'
    assert df.iloc[0]['result'] == '5'
    assert isinstance(df.iloc[0]['timestamp'], datetime.datetime)
    
    # Check second calculation
    assert df.iloc[1]['operation'] == 'Multiplication'
    assert df.iloc[1]['operand1'] == '4'
    assert df.iloc[1]['operand2'] == '5'
    assert df.iloc[1]['result'] == '20'
    assert isinstance(df.iloc[1]['timestamp'], datetime.datetime)

# Test REPL Commands (using patches for input/output handling)

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_calculator_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")

@patch('builtins.input', side_effect=['clear', 'history', 'exit'])
@patch('builtins.print')
def test_calculator_repl_history_empty(mock_print, mock_input):
    """Test history command when no calculations exist."""
    calculator_repl()
    mock_print.assert_any_call("History cleared")
    mock_print.assert_any_call("No calculations in history")

@patch('builtins.input', side_effect=['clear', 'add', '2', '3', 'history', 'exit'])
@patch('builtins.print')
def test_calculator_repl_history_with_calculations(mock_print, mock_input):
    """Test history command when calculations exist."""
    calculator_repl()
    mock_print.assert_any_call("\nCalculation History:")
    mock_print.assert_any_call("1. Addition(2, 3) = 5")

# Test Load Command
# Added by Greg Hoffer - with help of Claude

#Added testing for REPL load command because only load history was tested 
@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_calculator_repl_load_success(mock_print, mock_input):
    """Test successful load command in REPL."""
    with patch('app.calculator.Calculator.load_history') as mock_load_history:
        calculator_repl()
        # load_history is called twice: once during initialization, once for the load command
        assert mock_load_history.call_count == 2
        mock_print.assert_any_call("History loaded successfully")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['load', 'exit'])
@patch('builtins.print')
def test_calculator_repl_load_failure(mock_print, mock_input):
    """Test load command failure handling in REPL."""
    with patch('app.calculator.Calculator.load_history') as mock_load_history:
        # First call (during init) succeeds, second call (load command) fails
        mock_load_history.side_effect = [None, Exception("File not found")]
        calculator_repl()
        assert mock_load_history.call_count == 2
        mock_print.assert_any_call("Error loading history: File not found")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['load', 'history', 'exit'])
@patch('builtins.print')
def test_calculator_repl_load_and_view_history(mock_print, mock_input):
    """Test load command followed by viewing history."""
    # Mock successful load with some sample data
    with patch('app.calculator.Calculator.load_history') as mock_load_history:
        # We'll also need to mock the history to show something after loading
        with patch('app.calculator.Calculator.show_history') as mock_show_history:
            mock_show_history.return_value = ["Addition(5, 3) = 8", "Subtraction(10, 2) = 8"]
            
            calculator_repl()
            
            # load_history called twice: during init and load command
            assert mock_load_history.call_count == 2
            mock_print.assert_any_call("History loaded successfully")
            mock_print.assert_any_call("\nCalculation History:")
            mock_print.assert_any_call("1. Addition(5, 3) = 8")
            mock_print.assert_any_call("2. Subtraction(10, 2) = 8")
            mock_print.assert_any_call("Goodbye!")

# Test Redo Command
# added by Greg Hoffer - with help of Claude

# Added test for redo command in REPL, only calculator redo method was tested
@patch('builtins.input', side_effect=['redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_redo_nothing_to_redo(mock_print, mock_input):
    """Test redo command when there's nothing to redo."""
    with patch('app.calculator.Calculator.redo') as mock_redo:
        mock_redo.return_value = False  # Nothing to redo
        calculator_repl()
        mock_redo.assert_called_once()
        mock_print.assert_any_call("Nothing to redo")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_redo_success(mock_print, mock_input):
    """Test successful redo command."""
    with patch('app.calculator.Calculator.redo') as mock_redo:
        mock_redo.return_value = True  # Successful redo
        calculator_repl()
        mock_redo.assert_called_once()
        mock_print.assert_any_call("Operation redone")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['add', '5', '3', 'undo', 'redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_undo_redo_sequence(mock_print, mock_input):
    """Test a complete undo/redo sequence in REPL."""
    # This test doesn't mock the individual methods to test the full flow
    calculator_repl()
    
    # Verify the sequence of operations
    mock_print.assert_any_call("\nResult: 8")      # Initial calculation
    mock_print.assert_any_call("Operation undone")  # Undo message
    mock_print.assert_any_call("Operation redone")  # Redo message
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['undo', 'redo', 'redo', 'exit'])
@patch('builtins.print')
def test_calculator_repl_multiple_redo_attempts(mock_print, mock_input):
    """Test multiple redo attempts when there's nothing to redo."""
    calculator_repl()
    
    # First undo should show "Nothing to undo"
    mock_print.assert_any_call("Nothing to undo")
    # Both redo attempts should show "Nothing to redo"
    redo_calls = [call for call in mock_print.call_args_list 
                  if call.args and call.args[0] == "Nothing to redo"]
    assert len(redo_calls) >= 2
    mock_print.assert_any_call("Goodbye!")

# Test Interruption Handling
# Added by Greg Hoffer - with help of Claude

@patch('builtins.input')
@patch('builtins.print')
def test_calculator_repl_keyboard_interrupt(mock_print, mock_input):
    """Test handling of KeyboardInterrupt (Ctrl+C) during command input."""
    # Setup input to raise KeyboardInterrupt on first call, then exit
    mock_input.side_effect = [KeyboardInterrupt(), 'exit']
    
    calculator_repl()
    
    # Verify that the interruption was handled gracefully
    mock_print.assert_any_call("\nOperation cancelled")
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input')
@patch('builtins.print')
def test_calculator_repl_keyboard_interrupt_during_operation(mock_print, mock_input):
    """Test handling of KeyboardInterrupt during arithmetic operation input."""
    # Setup input to start an operation, then interrupt on number input
    mock_input.side_effect = ['add', KeyboardInterrupt(), 'exit']
    
    calculator_repl()
    
    # Verify that the interruption was handled gracefully
    mock_print.assert_any_call("\nOperation cancelled")
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input')
@patch('builtins.print')
def test_calculator_repl_eof_error(mock_print, mock_input):
    """Test handling of EOFError (Ctrl+D) during input."""
    # Setup input to raise EOFError
    mock_input.side_effect = EOFError()
    
    calculator_repl()
    
    # Verify that EOFError was handled gracefully
    mock_print.assert_any_call("\nInput terminated. Exiting...")

@patch('builtins.input')
@patch('builtins.print')
def test_calculator_repl_multiple_interrupts(mock_print, mock_input):
    """Test handling of multiple consecutive interruptions."""
    # Setup multiple interruptions followed by exit
    mock_input.side_effect = [
        KeyboardInterrupt(),  # First interrupt
        KeyboardInterrupt(),  # Second interrupt  
        'exit'               # Finally exit
    ]
    
    calculator_repl()
    
    # Verify that both interruptions were handled by checking call count
    operation_cancelled_calls = [call for call in mock_print.call_args_list 
                               if call.args and call.args[0] == "\nOperation cancelled"]
    assert len(operation_cancelled_calls) >= 2
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input')
@patch('builtins.print') 
def test_calculator_repl_interrupt_during_number_input(mock_print, mock_input):
    """Test KeyboardInterrupt specifically during number input for operations."""
    # Start operation, provide first number, then interrupt on second number
    mock_input.side_effect = ['multiply', '5', KeyboardInterrupt(), 'exit']
    
    calculator_repl()
    
    # Verify graceful handling
    mock_print.assert_any_call("\nOperation cancelled")
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input')
@patch('builtins.print')
def test_calculator_repl_general_exception_handling(mock_print, mock_input):
    """Test handling of unexpected exceptions during operation."""
    # Create a mock that raises a general exception, then exit
    mock_input.side_effect = [Exception("Unexpected error"), 'exit']
    
    calculator_repl()
    
    # Verify that the exception was caught and handled
    mock_print.assert_any_call("Error: Unexpected error")
    mock_print.assert_any_call("Goodbye!")

# Test Fatal Error Handling
# Added by Greg Hoffer - with help of Claude

@patch('app.calculator_repl.Calculator')
@patch('app.calculator_repl.logging.error')
@patch('builtins.print')
def test_calculator_repl_fatal_initialization_error(mock_print, mock_logging_error, mock_calculator):
    """Test handling of fatal errors during calculator initialization."""
    # Make Calculator initialization raise an exception
    mock_calculator.side_effect = Exception("Fatal initialization error")
    
    # The function should raise the exception after logging it
    with pytest.raises(Exception, match="Fatal initialization error"):
        calculator_repl()
    
    # Verify that the fatal error was reported to user and logged
    mock_print.assert_any_call("Fatal error: Fatal initialization error")
    mock_logging_error.assert_called_once_with("Fatal error in calculator REPL: Fatal initialization error")

@patch('app.calculator_repl.Calculator')
@patch('app.calculator_repl.logging.error')
@patch('builtins.print')
def test_calculator_repl_fatal_observer_error(mock_print, mock_logging_error, mock_calculator):
    """Test handling of fatal errors during observer setup."""
    # Create a calculator instance that raises error when adding observers
    mock_calc_instance = Mock()
    mock_calc_instance.add_observer.side_effect = Exception("Observer setup failed")
    mock_calculator.return_value = mock_calc_instance
    
    # The function should raise the exception after logging it
    with pytest.raises(Exception, match="Observer setup failed"):
        calculator_repl()
    
    # Verify that the fatal error was reported and logged
    mock_print.assert_any_call("Fatal error: Observer setup failed")
    mock_logging_error.assert_called_once_with("Fatal error in calculator REPL: Observer setup failed")

@patch('app.calculator_repl.logging.error')
@patch('builtins.print')
def test_calculator_repl_fatal_startup_print_error(mock_print, mock_logging_error):
    """Test handling of fatal errors during startup print statement."""
    # Make the initial print statement raise an exception
    mock_print.side_effect = [Exception("Print system failure"), None, None]
    
    # The function should raise the exception after logging it
    with pytest.raises(Exception, match="Print system failure"):
        calculator_repl()
    
    # Verify that the fatal error was reported and logged
    mock_print.assert_any_call("Fatal error: Print system failure")
    mock_logging_error.assert_called_once_with("Fatal error in calculator REPL: Print system failure")


# Tests for missing coverage lines - Added by Greg Hoffer

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit_save_history_failure(mock_print, mock_input):
    """Test exit command when save_history fails (lines 54-55)."""
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        mock_save_history.side_effect = Exception("Save failed")
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("Warning: Could not save history: Save failed")
        mock_print.assert_any_call("Goodbye!")

# Note: Lines 98-99 (save command failure) are complex to test due to 
# the way save_history is called in multiple places. The error handling
# code exists but would require more complex mocking to test properly.

@patch('builtins.input', side_effect=['add', 'cancel', 'exit'])
@patch('builtins.print')
def test_calculator_repl_cancel_first_number(mock_print, mock_input):
    """Test cancelling operation at first number input (lines 116-117)."""
    calculator_repl()
    mock_print.assert_any_call("\nEnter numbers (or 'cancel' to abort):")
    mock_print.assert_any_call("Operation cancelled")
    mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['add', '5', 'cancel', 'exit'])
@patch('builtins.print')
def test_calculator_repl_cancel_second_number(mock_print, mock_input):
    """Test cancelling operation at second number input (lines 120-121)."""
    calculator_repl()
    mock_print.assert_any_call("\nEnter numbers (or 'cancel' to abort):")
    mock_print.assert_any_call("Operation cancelled")
    mock_print.assert_any_call("Goodbye!")