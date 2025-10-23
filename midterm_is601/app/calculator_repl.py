########################
# Calculator REPL       #
########################

from decimal import Decimal
import logging

from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver
from app.operations import OperationFactory
from colorama import Fore, Style, init

def calculator_repl():
    """
    Command-line interface for the calculator.

    Implements a Read-Eval-Print Loop (REPL) that continuously prompts the user
    for commands, processes arithmetic operations, and manages calculation history.
    """
    try:
        # Initialize colorama for cross-platform colored terminal output
        init(autoreset=True)
        
        # Initialize the Calculator instance
        calc = Calculator()

        # Register observers for logging and auto-saving history
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))

        # Command abbreviation mapping
        command_aliases = {
            # Arithmetic operations abbreviations
            'a': 'add',
            '+': 'add',
            's': 'subtract',
            'sub': 'subtract',
            '-': 'subtract',
            'm': 'multiply',
            'mul': 'multiply',
            '*': 'multiply',
            'd': 'divide',
            'div': 'divide',
            '/': 'divide',
            'p': 'power',
            'pow': 'power',
            '^': 'power',
            '**': 'power',
            'mod': 'modulus',
            '%': 'modulus',
            'id': 'integer_division',
            'idiv': 'integer_division',
            '//': 'integer_division',
            'per': 'percentage',
            'pct': 'percentage',
            'ad': 'absolute_difference',
            'abs': 'absolute_difference',
            'absdiff': 'absolute_difference',
            'r': 'root',
            'rt': 'root',
            # System commands abbreviations
            'h': 'help',
            '?': 'help',
            'q': 'exit',
            'quit': 'exit',
            'x': 'exit',
            'hist': 'history',
            'c': 'clear',
            'u': 'undo',
            'z': 'redo',
        }

        print("Calculator started. Type 'help' for commands.")

        while True:
            try:
                # Prompt the user for a command
                command = input("\nEnter command: ").lower().strip()

                # Resolve command aliases/abbreviations
                original_command = command
                command = command_aliases.get(command, command)

                if command == 'help':
                    # Display available commands
                    print("\nAvailable commands:")
                    print("  Arithmetic Operations:")
                    print("    add (a, +) - Addition")
                    print("    subtract (s, sub, -) - Subtraction")
                    print("    multiply (m, mul, *) - Multiplication")
                    print("    divide (d, div, /) - Division")
                    print("    power (p, pow, ^, **) - Exponentiation")
                    print("    modulus (mod, %) - Remainder after division")
                    print("    integer_division (id, idiv, //) - Integer division")
                    print("    percentage (per, pct) - Calculate percentage")
                    print("    absolute_difference (ad, abs, absdiff) - Absolute difference")
                    print("    root (r, rt) - Calculate nth root")
                    print("  System Commands:")
                    print("    help (h, ?) - Show this help")
                    print("    history (hist) - Show calculation history")
                    print("    clear (c) - Clear calculation history")
                    print("    undo (u) - Undo the last calculation")
                    print("    redo (z) - Redo the last undone calculation")
                    print("    save - Save calculation history to file")
                    print("    load - Load calculation history from file")
                    print("    exit (q, quit, x) - Exit the calculator")
                    continue

                if command == 'exit':
                    # Attempt to save history before exiting
                    try:
                        calc.save_history()
                        print("History saved successfully.")
                    except Exception as e:
                        print(f"{Fore.RED}Warning: Could not save history: {e}")
                    print("Goodbye!")
                    break

                if command == 'history':
                    # Display calculation history
                    history = calc.show_history()
                    if not history:
                        print("No calculations in history")
                    else:
                        print("\nCalculation History:")
                        for i, entry in enumerate(history, 1):
                            print(f"{i}. {entry}")
                    continue

                if command == 'clear':
                    # Clear calculation history
                    calc.clear_history()
                    print("History cleared")
                    continue

                if command == 'undo':
                    # Undo the last calculation
                    if calc.undo():
                        print("Operation undone")
                    else:
                        print("Nothing to undo")
                    continue

                if command == 'redo':
                    # Redo the last undone calculation
                    if calc.redo():
                        print("Operation redone")
                    else:
                        print("Nothing to redo")
                    continue

                if command == 'save':
                    # Save calculation history to file
                    try:
                        calc.save_history()
                        print("History saved successfully") # pragma: no cover
                    except Exception as e:
                        print(f"{Fore.RED}Error saving history: {e}")
                    continue

                if command == 'load':
                    # Load calculation history from file
                    try:
                        calc.load_history()
                        print("History loaded successfully")
                    except Exception as e:
                        print(f"{Fore.RED}Error loading history: {e}")
                    continue

                if command in ['add', 'subtract', 'multiply', 'divide', 'power', 'modulus', 'integer_division', 'percentage', 'absolute_difference', 'root']:
                    # Perform the specified arithmetic operation
                    try:
                        print("\nEnter numbers (or 'cancel' to abort):")
                        a = input("First number: ")
                        if a.lower() == 'cancel':
                            print("Operation cancelled")
                            continue
                        b = input("Second number: ")
                        if b.lower() == 'cancel':
                            print("Operation cancelled")
                            continue

                        # Create the appropriate operation instance using the Factory pattern
                        operation = OperationFactory.create_operation(command)
                        calc.set_operation(operation)

                        # Perform the calculation
                        result = calc.perform_operation(a, b)

                        # Format the result with configured precision
                        if isinstance(result, Decimal):
                            try:
                                # Format result to configured precision
                                precision_pattern = Decimal('0.' + '0' * calc.config.precision)
                                formatted_result = str(result.quantize(precision_pattern).normalize())
                            except:# pragma: no cover
                                # Fallback if quantize fails
                                formatted_result = str(result)
                        else:
                            formatted_result = str(result)

                        print(f"\nResult: {formatted_result}")
                    except (ValidationError, OperationError) as e:
                        # Handle known exceptions related to validation or operation errors
                        print(f"{Fore.RED}Error: {e}")
                    except Exception as e:
                        # Handle any unexpected exceptions
                        print(f"{Fore.RED}Unexpected error: {e}")
                    continue

                # Handle unknown commands
                print(f"{Fore.RED}Unknown command: '{command}'. Type 'help' for available commands.")

            except KeyboardInterrupt:
                # Handle Ctrl+C interruption gracefully
                print(f"\n{Fore.RED}Operation cancelled")
                continue
            except EOFError:
                # Handle end-of-file (e.g., Ctrl+D) gracefully
                print(f"\n{Fore.RED}Input terminated. Exiting...")
                break
            except Exception as e:
                # Handle any other unexpected exceptions
                print(f"{Fore.RED}Error: {e}")
                continue

    except Exception as e:
        # Handle fatal errors during initialization
        print(f"{Fore.RED}Fatal error: {e}")
        logging.error(f"Fatal error in calculator REPL: {e}")
        raise
