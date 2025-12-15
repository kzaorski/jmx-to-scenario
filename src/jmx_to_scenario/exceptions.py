"""Custom exceptions for JMX to pt_scenario.yaml converter."""


class JMXConverterException(Exception):
    """Base exception for JMX converter errors."""

    def __init__(self, message: str, details: str | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class JMXParseException(JMXConverterException):
    """Exception raised when JMX file parsing fails."""

    pass


class ConversionException(JMXConverterException):
    """Exception raised when conversion logic fails."""

    pass


class OutputException(JMXConverterException):
    """Exception raised when YAML output fails."""

    pass
