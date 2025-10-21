copied repo from assignment 5 for the calculator app for midterm
added new commands to REPL interface and operations
    added modulus, integer division, percentage, and absolute difference
added testing for all new operations
added tests for some exception handling in REPL

New commands were cumbersome to type, added command abbreviations for operations and system inputs

revised result to accept precision setting in .env
revised history to read precision setting in .env

implemented colorama to display invalid input and error messages in RED

I think I created one too many folders so that the app is nested in one extra folder level in github.
    *not sure how to fix


HELP MENU PREVIEW

Available commands:
  Arithmetic Operations:
    add (a, +) - Addition
    subtract (s, sub, -) - Subtraction
    multiply (m, mul, *) - Multiplication
    divide (d, div, /) - Division
    power (p, pow, ^, **) - Exponentiation
    modulus (mod, %) - Remainder after division
    integer_division (id, idiv, //) - Integer division
    percentage (per, pct) - Calculate percentage
    absolute_difference (ad, abs, absdiff) - Absolute difference
    root (r, rt) - Calculate nth root
  System Commands:
    help (h, ?) - Show this help
    history (hist) - Show calculation history
    clear (c) - Clear calculation history
    undo (u) - Undo the last calculation
    redo (z) - Redo the last undone calculation
    save - Save calculation history to file
    load - Load calculation history from file
    exit (q, quit, x) - Exit the calculator

