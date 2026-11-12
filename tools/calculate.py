"""calculate tool: safely evaluate an arithmetic expression."""
import re

ALLOWED = re.compile(r'^[\d\s+\-*/%().]+$')


def calculate(expression):
    """
    Evaluate an arithmetic expression and return the result as a string.

    Only digits, spaces, parentheses, decimal points, and + - * / %
    are allowed. Names and function calls are rejected.

    >>> calculate('2 + 3 * 4')
    '14'
    >>> calculate('(2 + 3) * 4')
    '20'
    >>> calculate('10 / 4')
    '2.5'
    >>> calculate('7 % 3')
    '1'
    >>> calculate('1 / 0')
    'Error: division by zero'
    >>> calculate('2 +')
    'Error: invalid expression'
    >>> calculate('__import__("os")')
    'Error: only numbers and + - * / % ( ) are allowed'
    >>> calculate('abs(-3)')
    'Error: only numbers and + - * / % ( ) are allowed'
    """
    if not ALLOWED.match(expression):
        return 'Error: only numbers and + - * / % ( ) are allowed'
    try:
        result = eval(expression, {'__builtins__': {}}, {})
    except ZeroDivisionError:
        return 'Error: division by zero'
    except SyntaxError:
        return 'Error: invalid expression'
    return str(result)
