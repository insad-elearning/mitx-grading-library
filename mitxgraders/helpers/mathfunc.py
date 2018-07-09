"""
mathfunc.py

Contains mathematical functions for use in interpreting formulas.

Contains some helper functions used in grading formulae:
* within_tolerance

Defines:
* DEFAULT_FUNCTIONS
* DEFAULT_VARIABLES
* DEFAULT_SUFFIXES
* METRIC_SUFFIXES
"""
from __future__ import division
import math
from numbers import Number
import numpy as np
import scipy.special as special
from mitxgraders.baseclasses import StudentFacingError
from mitxgraders.helpers.validatorfuncs import get_number_of_args

class DomainError(StudentFacingError):
    """
    Raised when a function has domain error.
    """

def is_scalar(arg):
    """
    Tests if arg is Number or scalar numpy array.

    >>> map(is_scalar, [3, 4 + 2j, 4.2, np.array(5)])
    [True, True, True, True]
    >>> is_scalar(np.array([4, 7]))
    False

    """
    if isinstance(arg, Number):
        return True
    elif isinstance(arg, np.ndarray) and arg.ndim == 0:
        return True

    return False

# QUESTION @Jolyon If you can think of a better way to raise errors when
# sin(A), cos(A), etc is handed, I'm all-ears!
def scalar_domain(display_name):
    """
    Returns a function decorator that causes function to raises a DomainError
    if function is called is called with a non-scalar argument. DomainError
    refers to function by its given display_name.

    >>> @scalar_domain('plus3')
    ... def f(x):
    ...     return x + 3
    >>> f(4)
    7
    >>> f([5, 2])
    Traceback (most recent call last):
    DomainError: Function 'plus3(...)' only accepts scalar inputs, but was given a non-scalar input.

    For now, scalar_domain() only accepts unary functions:
    >>> @scalar_domain('add')
    ... def f(x, y):
    ...     return x + y
    Traceback (most recent call last):
    ValueError: Decorator 'scalar_domain' can only be used with unary functions.

    Comment: The n-argument case seems intractable because it breaks get_number_of_args,
    which is used in calc.py. But we could hard-code the n=1, n=2, n=3 cases.
    Anything larger probably wouldn't come up in practice.
    """

    def _decorator(func):
        if get_number_of_args(func) > 1:
            raise ValueError("Decorator 'scalar_domain' can only be used with unary functions.")

        # can't use @wraps, doesn't work with callable classes like numpy ufuncs
        def _func(arg):
            if not is_scalar(arg):
                raise DomainError("Function '{0}(...)' only accepts scalar inputs, but "
                                      "was given a non-scalar input.".format(display_name))

            return func(arg)

        _func.__name__ = func.__name__

        return _func

    return _decorator

# Normal Trig
def sec(arg):
    """Secant"""
    return 1 / np.cos(arg)

def csc(arg):
    """Cosecant"""
    return 1 / np.sin(arg)

def cot(arg):
    """Cotangent"""
    return 1 / np.tan(arg)

# Inverse Trig
# http://en.wikipedia.org/wiki/Inverse_trigonometric_functions#Relationships_among_the_inverse_trigonometric_functions
def arcsec(val):
    """Inverse secant"""
    return np.arccos(1. / val)

def arccsc(val):
    """Inverse cosecant"""
    return np.arcsin(1. / val)

def arccot(val):
    """Inverse cotangent"""
    if np.real(val) < 0:
        return -np.pi / 2 - np.arctan(val)
    else:
        return np.pi / 2 - np.arctan(val)

# Hyperbolic Trig
def sech(arg):
    """Hyperbolic secant"""
    return 1 / np.cosh(arg)

def csch(arg):
    """Hyperbolic cosecant"""
    return 1 / np.sinh(arg)

def coth(arg):
    """Hyperbolic cotangent"""
    return 1 / np.tanh(arg)

# And their inverses
def arcsech(val):
    """Inverse hyperbolic secant"""
    return np.arccosh(1. / val)

def arccsch(val):
    """Inverse hyperbolic cosecant"""
    return np.arcsinh(1. / val)

def arccoth(val):
    """Inverse hyperbolic cotangent"""
    return np.arctanh(1. / val)

def real(z):
    """
    Returns the real part of z.
    >>> real(2+3j)
    2.0

    Note: We convert to float because numpy returns scalar arrays:
    >>> isinstance(np.real(2+3j), np.ndarray)
    True
    """
    return float(np.real(z))

def imag(z):
    """
    Returns the imaginary part of z.
    >>> imag(2+3j)
    3.0

    >>> isinstance(np.imag(2+3j), np.ndarray)
    True
    """
    return float(np.imag(z))

def factorial(z):
    """
    Factorial function over complex numbers.

    Usage
    =====

    Non-negative integer input returns integers:
    >>> factorial(4)
    24

    Floats and complex numbers use scipy's gamma function:
    >>> factorial(0.5) # doctest: +ELLIPSIS
    0.8862269...
    >>> math.sqrt(math.pi)/2
    0.8862269...
    >>> factorial(3.2+4.1j)
    (1.0703272...-0.3028032...j)
    >>> factorial(2.2+4.1j)*(3.2+4.1j)
    (1.0703272...-0.3028032...j)

    Works with numpy arrays:
    >>> np.array_equal(
    ...     factorial(np.array([1, 2, 3, 4])),
    ...     np.array([1, 2, 6, 24])
    ... )
    True

    Throws errors at poles:
    >>> factorial(-2)
    Traceback (most recent call last):
    ValueError: factorial() not defined for negative values

    """

    try:
        is_integer = isinstance(z, int) or z.is_integer()
    except AttributeError:
        is_integer = False

    if is_integer:
        return math.factorial(z)

    value = special.gamma(z+1)
    # value is a numpy array; If it's 0d, we can just get its item:
    try:
        return value.item()
    except ValueError:
        return value

# Variables available by default
DEFAULT_VARIABLES = {
    'i': np.complex(0, 1),
    'j': np.complex(0, 1),
    'e': np.e,
    'pi': np.pi
}

# Functions available by default
# We use scimath variants which give complex results when needed. For example:
#   np.sqrt(-4+0j) = 2j
#   np.sqrt(-4) = nan, but
#   np.lib.scimath.sqrt(-4) = 2j

UNSAFE_SCALAR_FUNCTIONS = {
    'sin': np.sin,
    'cos': np.cos,
    'tan': np.tan,
    'sec': sec,
    'csc': csc,
    'cot': cot,
    'sqrt': np.lib.scimath.sqrt,
    'log10': np.lib.scimath.log10,
    'log2': np.lib.scimath.log2,
    'ln': np.lib.scimath.log,
    'exp': np.exp,
    'arccos': np.lib.scimath.arccos,
    'arcsin': np.lib.scimath.arcsin,
    'arctan': np.arctan,
    'arcsec': arcsec,
    'arccsc': arccsc,
    'arccot': arccot,
    'abs': np.abs,
    'fact': factorial,
    'factorial': factorial,
    'sinh': np.sinh,
    'cosh': np.cosh,
    'tanh': np.tanh,
    'sech': sech,
    'csch': csch,
    'coth': coth,
    'arcsinh': np.arcsinh,
    'arccosh': np.arccosh,
    'arctanh': np.lib.scimath.arctanh,
    'arcsech': arcsech,
    'arccsch': arccsch,
    'arccoth': arccoth
}

SCALAR_FUNCTIONS = {key: scalar_domain(key)(UNSAFE_SCALAR_FUNCTIONS[key])
                    for key in UNSAFE_SCALAR_FUNCTIONS}

ARRAY_FUNCTIONS = {
    're': real,
    'im': imag,
    'conj': np.conj,
}

def merge_dicts(*dict_args):
    """Merge an arbitrary number of dictionaries."""
    merged = {}
    for dict_arg in dict_args:
        merged.update(dict_arg)
    return merged

DEFAULT_FUNCTIONS = merge_dicts(SCALAR_FUNCTIONS, ARRAY_FUNCTIONS)

DEFAULT_SUFFIXES = {
    '%': 0.01
}

METRIC_SUFFIXES = {
    'k': 1e3, 'M': 1e6, 'G': 1e9, 'T': 1e12,
    'm': 1e-3, 'u': 1e-6, 'n': 1e-9, 'p': 1e-12
}

def robust_pow(base, exponent):
    """
    Calculates __pow__, and tries other approachs if that doesn't work.

    Usage:
    ======

    >>> robust_pow(5, 2)
    25
    >>> robust_pow(0.5, -1)
    2.0

    If base is negative and power is fractional, complex results are returned:
    >>> almost_j = robust_pow(-1, 0.5)
    >>> np.allclose(almost_j, 1j)
    True
    """
    try:
        return base ** exponent
    except ValueError:
        return np.lib.scimath.power(base, exponent)

def within_tolerance(x, y, tolerance):
    """
    Check that |x-y| <= tolerance with appropriate norm.

    Args:
        x: number or array (np array_like)
        y: number or array (np array_like)
        tolerance: Number or PercentageString

    Usage
    =====

    The tolerance can be a number:
    >>> within_tolerance(10, 9.01, 1)
    True
    >>> within_tolerance(10, 9.01, 0.5)
    False

    If tolerance is a percentage, it is a percent of (the norm of) x:
    >>> within_tolerance(10, 9.01, '10%')
    True
    >>> within_tolerance(9.01, 10, '10%')
    False

    Works for vectors and matrices:
    >>> A = np.matrix([[1,2],[-3,1]])
    >>> B = np.matrix([[1.1, 2], [-2.8, 1]])
    >>> diff = round(np.linalg.norm(A-B), 6)
    >>> diff
    0.223607
    >>> within_tolerance(A, B, 0.25)
    True

    If x - y raises a StudentFacingError, then subtraction of these types
    is intentionally not supported and (x, y) are not within_tolerance:
    >>> class Foo():
    ...     def __sub__(self, other): raise StudentFacingError()
    ...     def __rsub__(self, other): raise StudentFacingError()
    >>> within_tolerance(0, Foo(), '1%')
    False
    """
    # When used within graders, tolerance has already been
    # validated as a Number or PercentageString
    if isinstance(tolerance, str):
        # Construct percentage tolerance
        tolerance = tolerance.strip()
        tolerance = np.linalg.norm(x) * float(tolerance[:-1]) * 0.01

    try:
        difference = x - y
    except StudentFacingError:
        # Apparently, the answer and the student_input cannot be compared.
        return False

    return np.linalg.norm(difference) <= tolerance
