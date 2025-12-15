"""Groovy/JavaScript expression to pt_scenario condition converter."""

import re


def convert_groovy_to_condition(groovy_expr: str) -> tuple[str, int | None, list[str]]:
    """Convert Groovy/JavaScript condition to pt_scenario while condition format.

    Supports common patterns:
    - ${__groovy(vars.get('varName') != 'value')}
    - vars.get('varName') != 'value'
    - ${varName} != 'value'
    - ${__javaScript("${count}" < "10")}

    Args:
        groovy_expr: Groovy/JavaScript expression string

    Returns:
        Tuple of (condition_string, max_iterations, warnings_list)
    """
    warnings: list[str] = []
    max_iterations: int | None = None

    # Pattern 1: ${__groovy(vars.get('varName') != 'value')}
    match = re.search(
        r"\$\{__groovy\(vars\.get\(['\"](\w+)['\"]\)\s*(!=|==)\s*['\"]([^'\"]+)['\"]\)\}",
        groovy_expr,
    )
    if match:
        var_name, operator, value = match.groups()
        # Extract iteration limit if present
        max_iterations = _extract_iteration_limit(groovy_expr)
        return f"${{{var_name}}} {operator} '{value}'", max_iterations, warnings

    # Pattern 2: vars.get('varName') != 'value' (without wrapper)
    match = re.search(
        r"vars\.get\(['\"](\w+)['\"]\)\s*(!=|==)\s*['\"]([^'\"]+)['\"]",
        groovy_expr,
    )
    if match:
        var_name, operator, value = match.groups()
        max_iterations = _extract_iteration_limit(groovy_expr)
        return f"${{{var_name}}} {operator} '{value}'", max_iterations, warnings

    # Pattern 3: ${varName} != 'value'
    match = re.search(
        r"\$\{(\w+)\}\s*(!=|==)\s*['\"]([^'\"]+)['\"]",
        groovy_expr,
    )
    if match:
        var_name, operator, value = match.groups()
        return f"${{{var_name}}} {operator} '{value}'", max_iterations, warnings

    # Pattern 4: JavaScript comparison "${count}" < "10"
    match = re.search(
        r"\$\{__javaScript\(['\"]?\$\{(\w+)\}['\"]?\s*([<>=!]+)\s*['\"]?(\d+)['\"]?\)\}",
        groovy_expr,
    )
    if match:
        var_name, operator, value = match.groups()
        return f"${{{var_name}}} {operator} {value}", int(value), warnings

    # Pattern 5: Simple ${varName} comparison without quotes
    match = re.search(
        r"\$\{(\w+)\}\s*(!=|==|<|>|<=|>=)\s*(\d+)",
        groovy_expr,
    )
    if match:
        var_name, operator, value = match.groups()
        return f"${{{var_name}}} {operator} {value}", None, warnings

    # Cannot convert - return original with warning
    warnings.append(f"Could not convert Groovy expression: {groovy_expr}")
    return groovy_expr, max_iterations, warnings


def _extract_iteration_limit(expr: str) -> int | None:
    """Extract iteration limit from Groovy expression.

    Looks for patterns like:
    - getIteration() <= 100
    - vars.getIteration() < 50

    Args:
        expr: Groovy expression

    Returns:
        Iteration limit or None
    """
    match = re.search(r"getIteration\(\)\s*<=?\s*(\d+)", expr)
    if match:
        return int(match.group(1))

    match = re.search(r"getIteration\(\)\s*<\s*(\d+)", expr)
    if match:
        # For < operator, the limit is value - 1
        return int(match.group(1))

    return None


def convert_match_number(match_numbers: str) -> tuple[str, list[str]]:
    """Convert JMX match_numbers to pt_scenario match value.

    Args:
        match_numbers: JMX JSONPostProcessor match_numbers value

    Returns:
        Tuple of (match_value, warnings_list)
    """
    warnings: list[str] = []

    if not match_numbers or match_numbers.strip() == "":
        return "first", warnings

    try:
        num = int(match_numbers)
    except ValueError:
        warnings.append(f"Invalid match_numbers value: {match_numbers}, using 'first'")
        return "first", warnings

    if num == 1:
        return "first", warnings
    elif num == -1:
        return "all", warnings
    elif num == 0:
        # Random match - not supported, use first
        warnings.append("match_numbers=0 (random) converted to 'first'")
        return "first", warnings
    else:
        # N-th match - not supported, use first
        warnings.append(f"match_numbers={num} (N-th) converted to 'first' (not supported)")
        return "first", warnings
