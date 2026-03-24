import math
import re

def parse_latex_math(text):
    """
    Very basic conversion of LaTeX math to python-ish expressions for sympy.
    """
    # Replace common LaTeX commands
    text = text.replace(r'\times', '*')
    text = text.replace(r'\cdot', '*')
    text = text.replace(r'\div', '/')
    text = text.replace(r'\^', '**')
    text = text.replace(r'\{', '(')
    text = text.replace(r'\}', ')')

    # \frac{a}{b} -> ((a)/(b))
    text = re.sub(r'\\frac\s*\((.*?)\)\s*\((.*?)\)', r'((\1)/(\2))', text)

    # \binom{n}{k} -> binomial(n, k)
    text = re.sub(r'\\binom\s*\((.*?)\)\s*\((.*?)\)', r'binomial(\1,\2)', text)

    # \lfloor x \rfloor -> floor(x)
    text = re.sub(r'\\leftlfloor(.*?)\\rightrfloor', r'floor(\1)', text)

    # Remove remaining backslashes
    text = text.replace('\\', ' ')

    return text

def integer_valuation(n, p):
    """v_p(n)"""
    if n == 0: return float('inf')
    count = 0
    while n % p == 0:
        count += 1
        n //= p
    return count

def legendre_valuation(n, p):
    """v_p(n!)"""
    res = 0
    while n > 0:
        n //= p
        res += n
    return res
