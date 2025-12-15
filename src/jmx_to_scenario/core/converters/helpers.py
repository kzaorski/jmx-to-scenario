"""XML property extraction helpers for JMX parsing."""

from xml.etree.ElementTree import Element


def get_string_prop(element: Element, name: str, default: str = "") -> str:
    """Get stringProp value by name from JMX element.

    Args:
        element: XML element to search in
        name: Property name attribute value
        default: Default value if not found

    Returns:
        Property text value or default
    """
    prop = element.find(f"stringProp[@name='{name}']")
    if prop is not None and prop.text:
        return prop.text
    return default


def get_bool_prop(element: Element, name: str, default: bool = False) -> bool:
    """Get boolProp value by name from JMX element.

    Args:
        element: XML element to search in
        name: Property name attribute value
        default: Default value if not found

    Returns:
        Boolean value or default
    """
    prop = element.find(f"boolProp[@name='{name}']")
    if prop is not None and prop.text:
        return prop.text.lower() == "true"
    return default


def get_int_prop(element: Element, name: str, default: int = 0) -> int:
    """Get intProp or stringProp as int from JMX element.

    JMeter sometimes stores numbers as stringProp, so we check both.

    Args:
        element: XML element to search in
        name: Property name attribute value
        default: Default value if not found or invalid

    Returns:
        Integer value or default
    """
    # Try intProp first
    prop = element.find(f"intProp[@name='{name}']")
    if prop is not None and prop.text:
        try:
            return int(prop.text)
        except ValueError:
            pass

    # Try stringProp (JMeter sometimes uses string for numbers)
    prop = element.find(f"stringProp[@name='{name}']")
    if prop is not None and prop.text:
        try:
            return int(prop.text)
        except ValueError:
            pass

    return default


def get_attribute(element: Element, name: str, default: str = "") -> str:
    """Get attribute value from XML element.

    Args:
        element: XML element
        name: Attribute name
        default: Default value if not found

    Returns:
        Attribute value or default
    """
    return element.get(name, default)


def is_enabled(element: Element) -> bool:
    """Check if JMX element is enabled.

    Args:
        element: XML element with optional 'enabled' attribute

    Returns:
        True if enabled or attribute not present, False otherwise
    """
    enabled = element.get("enabled", "true")
    return enabled.lower() == "true"


def normalize_variable_refs(text: str) -> str:
    """Normalize variable references in text.

    JMX uses $${varName} to escape ${varName} in some contexts.
    pt_scenario uses ${varName}.

    Args:
        text: Text potentially containing variable references

    Returns:
        Normalized text with ${varName} format
    """
    if not text:
        return text

    # Replace escaped $${var} with ${var}
    return text.replace("$${", "${")


def strip_carriage_returns(text: str) -> str:
    """Strip carriage returns from text.

    JMX files often contain Windows-style line endings.

    Args:
        text: Text with potential carriage returns

    Returns:
        Text with carriage returns removed
    """
    if not text:
        return text
    return text.replace("\r", "")
