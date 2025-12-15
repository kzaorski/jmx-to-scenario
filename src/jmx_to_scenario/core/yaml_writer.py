"""YAML writer for pt_scenario.yaml output."""

from pathlib import Path
from typing import Any

import yaml

from jmx_to_scenario.core.data_types import ParsedScenario, ScenarioStep
from jmx_to_scenario.exceptions import OutputException


class YAMLWriter:
    """Write ParsedScenario to pt_scenario.yaml format."""

    def write(self, scenario: ParsedScenario, output_path: str) -> None:
        """Write scenario to YAML file.

        Args:
            scenario: ParsedScenario to write
            output_path: Path to output file

        Raises:
            OutputException: If writing fails
        """
        try:
            data = self._build_yaml_dict(scenario)

            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=100,
                    Dumper=self._get_custom_dumper(),
                )
        except OSError as e:
            raise OutputException("Failed to write YAML file", str(e)) from e

    def to_string(self, scenario: ParsedScenario) -> str:
        """Convert scenario to YAML string.

        Args:
            scenario: ParsedScenario to convert

        Returns:
            YAML string
        """
        data = self._build_yaml_dict(scenario)

        return yaml.dump(
            data,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
            width=100,
            Dumper=self._get_custom_dumper(),
        )

    def _build_yaml_dict(self, scenario: ParsedScenario) -> dict[str, Any]:
        """Build dictionary for YAML output.

        Args:
            scenario: ParsedScenario to convert

        Returns:
            Dictionary ready for YAML serialization
        """
        data: dict[str, Any] = {"name": scenario.name}

        if scenario.description:
            data["description"] = scenario.description

        # Add settings if non-default
        settings_dict = self._format_settings(scenario.settings)
        if settings_dict:
            data["settings"] = settings_dict

        # Add variables if present
        if scenario.variables:
            data["variables"] = scenario.variables

        # Add scenario steps
        data["scenario"] = [self._format_step(step) for step in scenario.steps]

        return data

    def _format_settings(self, settings: Any) -> dict[str, Any]:
        """Format settings for YAML output, omitting defaults.

        Args:
            settings: ScenarioSettings object

        Returns:
            Dictionary with non-default settings
        """
        result: dict[str, Any] = {}

        if settings.threads != 1:
            result["threads"] = settings.threads

        if settings.rampup != 0:
            result["rampup"] = settings.rampup

        if settings.loops is not None and settings.loops != 1:
            result["loops"] = settings.loops

        if settings.duration is not None:
            result["duration"] = settings.duration

        if settings.base_url:
            result["base_url"] = settings.base_url

        return result

    def _format_step(self, step: ScenarioStep) -> dict[str, Any]:
        """Format a single step for YAML output.

        Args:
            step: ScenarioStep to format

        Returns:
            Dictionary for YAML step
        """
        result: dict[str, Any] = {
            "name": step.name,
            "endpoint": step.endpoint,
        }

        # Only include enabled if False
        if not step.enabled:
            result["enabled"] = False

        # Add headers if present
        if step.headers:
            result["headers"] = step.headers

        # Add params if present
        if step.params:
            result["params"] = step.params

        # Add payload if present
        if step.payload is not None:
            result["payload"] = step.payload

        # Add capture if present
        if step.capture:
            result["capture"] = step.capture

        # Add assert if present
        if step.assert_config:
            result["assert"] = step.assert_config

        # Add loop if present
        if step.loop:
            result["loop"] = step.loop

        # Add think_time if present
        if step.think_time is not None:
            result["think_time"] = step.think_time

        return result

    def _get_custom_dumper(self) -> type:
        """Get custom YAML dumper with proper formatting.

        Returns:
            Custom Dumper class
        """

        class CustomDumper(yaml.SafeDumper):
            pass

        # Represent None as empty string
        def represent_none(dumper: yaml.Dumper, data: None) -> yaml.ScalarNode:
            return dumper.represent_scalar("tag:yaml.org,2002:null", "")

        CustomDumper.add_representer(type(None), represent_none)

        # Use literal style for multiline strings
        def represent_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
            if "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        CustomDumper.add_representer(str, represent_str)

        return CustomDumper
