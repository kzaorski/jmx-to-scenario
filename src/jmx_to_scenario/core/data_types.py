"""Data types for JMX to pt_scenario.yaml conversion."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class JMXDefaults:
    """HTTP Request Defaults extracted from JMX ConfigTestElement."""

    domain: str = ""
    port: str = ""
    protocol: str = "http"
    content_encoding: str = "UTF-8"


@dataclass
class CaptureConfig:
    """Variable capture configuration from JSONPostProcessor."""

    variable_name: str
    jsonpath: str
    match: str = "first"  # "first", "all"


@dataclass
class AssertConfig:
    """Assertion configuration from ResponseAssertion/JSONPathAssertion."""

    status: int | None = None
    body: dict[str, Any] = field(default_factory=dict)
    body_contains: list[str] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)


@dataclass
class LoopConfig:
    """Loop configuration from LoopController/WhileController."""

    count: int | None = None
    while_condition: str | None = None
    max_iterations: int = 100
    interval: int | None = None
    variable: str | None = None


@dataclass
class ExtractedSampler:
    """Intermediate representation of HTTP sampler from JMX."""

    name: str
    method: str
    path: str
    enabled: bool = True
    domain: str = ""
    port: str = ""
    protocol: str = ""
    payload: dict[str, Any] | str | None = None
    params: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    captures: list[CaptureConfig] = field(default_factory=list)
    assertions: AssertConfig | None = None
    loop: LoopConfig | None = None
    think_time: int | None = None


@dataclass
class ScenarioSettings:
    """Test execution settings from ThreadGroup."""

    threads: int = 1
    rampup: int = 0
    loops: int | None = None
    duration: int | None = None
    base_url: str | None = None


@dataclass
class ScenarioStep:
    """A step in the pt_scenario.yaml output."""

    name: str
    endpoint: str  # "METHOD /path" format
    enabled: bool = True
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] | str | None = None
    capture: list[dict[str, Any] | str] = field(default_factory=list)
    assert_config: dict[str, Any] | None = None
    loop: dict[str, Any] | None = None
    think_time: int | None = None


@dataclass
class ParsedScenario:
    """Complete parsed scenario ready for YAML output."""

    name: str
    description: str | None = None
    settings: ScenarioSettings = field(default_factory=ScenarioSettings)
    variables: dict[str, str] = field(default_factory=dict)
    steps: list[ScenarioStep] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of JMX import operation."""

    success: bool
    scenario: ParsedScenario | None = None
    yaml_path: str | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
