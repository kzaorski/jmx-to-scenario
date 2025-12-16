"""Scenario builder for converting extracted samplers to pt_scenario format."""

from typing import Any

from jmx_to_scenario.core.data_types import (
    CaptureConfig,
    ExtractedSampler,
    FileConfig,
    ParsedScenario,
    ScenarioSettings,
    ScenarioStep,
)


class ScenarioBuilder:
    """Build ParsedScenario from extracted JMX data."""

    def __init__(self) -> None:
        self._warnings: list[str] = []

    def build(
        self,
        name: str,
        samplers: list[ExtractedSampler],
        settings: ScenarioSettings,
        variables: dict[str, str],
        description: str | None = None,
    ) -> ParsedScenario:
        """Build a ParsedScenario from extracted data.

        Args:
            name: Scenario name
            samplers: List of extracted samplers
            settings: Test settings
            variables: User-defined variables
            description: Optional description

        Returns:
            ParsedScenario ready for YAML output
        """
        steps: list[ScenarioStep] = []
        for sampler in samplers:
            # Create main step (without think_time - it will be separate)
            main_step = self._sampler_to_step(sampler, include_think_time=False)
            steps.append(main_step)

            # If sampler has think_time, create a separate think_time step
            if sampler.think_time is not None:
                think_time_step = ScenarioStep(
                    name="Think Time",
                    endpoint=None,
                    think_time=sampler.think_time,
                )
                steps.append(think_time_step)

        return ParsedScenario(
            name=name,
            description=description,
            settings=settings,
            variables=variables,
            steps=steps,
        )

    def get_warnings(self) -> list[str]:
        """Get accumulated warnings."""
        return self._warnings

    def _sampler_to_step(
        self, sampler: ExtractedSampler, include_think_time: bool = True
    ) -> ScenarioStep:
        """Convert ExtractedSampler to ScenarioStep.

        Args:
            sampler: Extracted sampler data
            include_think_time: Whether to include think_time in this step.
                               Set to False when think_time will be a separate step.

        Returns:
            ScenarioStep for YAML output
        """
        # Build endpoint string: "METHOD /path"
        endpoint = f"{sampler.method} {sampler.path}"

        # Convert captures to YAML format
        capture = self._format_captures(sampler.captures)

        # Convert assertions to YAML format
        assert_config = self._format_assertions(sampler.assertions)

        # Convert loop to YAML format
        loop = self._format_loop(sampler.loop)

        # Filter out empty headers
        headers = {k: v for k, v in sampler.headers.items() if v}

        # Filter out empty params
        params = {k: v for k, v in sampler.params.items() if v}

        # Convert files to YAML format
        files = self._format_files(sampler.files)

        return ScenarioStep(
            name=sampler.name,
            endpoint=endpoint,
            enabled=sampler.enabled,
            headers=headers if headers else {},
            params=params if params else {},
            payload=sampler.payload,
            files=files,
            capture=capture,
            assert_config=assert_config,
            loop=loop,
            think_time=sampler.think_time if include_think_time else None,
            random=sampler.random,
        )

    def _format_captures(self, captures: list[CaptureConfig]) -> list[dict[str, Any] | str]:
        """Format captures for YAML output.

        Args:
            captures: List of CaptureConfig objects

        Returns:
            List of capture entries in YAML format
        """
        result: list[dict[str, Any] | str] = []

        for capture in captures:
            # Check if we can use simplified format
            if capture.match == "first" and capture.jsonpath == f"$.{capture.variable_name}":
                # Simple format: just variable name
                result.append(capture.variable_name)
            elif capture.match == "first" and capture.jsonpath.startswith("$."):
                # Mapped format: varName: "field"
                field = capture.jsonpath[2:]  # Remove "$."
                if "." not in field and "[" not in field:
                    result.append({capture.variable_name: field})
                else:
                    # Explicit format with path
                    result.append({
                        capture.variable_name: {
                            "path": capture.jsonpath,
                        }
                    })
            else:
                # Explicit format with path and match
                capture_dict: dict[str, Any] = {"path": capture.jsonpath}
                if capture.match != "first":
                    capture_dict["match"] = capture.match
                result.append({capture.variable_name: capture_dict})

        return result

    def _format_assertions(
        self, assertions: Any | None
    ) -> dict[str, Any] | None:
        """Format assertions for YAML output.

        Args:
            assertions: AssertConfig or None

        Returns:
            Dictionary for YAML assert section or None
        """
        if assertions is None:
            return None

        result: dict[str, Any] = {}

        if assertions.status is not None:
            result["status"] = assertions.status

        if assertions.body:
            result["body"] = assertions.body

        if assertions.body_contains:
            result["body_contains"] = assertions.body_contains

        if assertions.headers:
            result["headers"] = assertions.headers

        return result if result else None

    def _format_loop(self, loop: Any | None) -> dict[str, Any] | None:
        """Format loop configuration for YAML output.

        Args:
            loop: LoopConfig or None

        Returns:
            Dictionary for YAML loop section or None
        """
        if loop is None:
            return None

        result: dict[str, Any] = {}

        if loop.count is not None:
            result["count"] = loop.count

        if loop.while_condition is not None:
            result["while"] = loop.while_condition

        if loop.max_iterations and loop.max_iterations != 100:
            result["max"] = loop.max_iterations

        if loop.interval is not None:
            result["interval"] = loop.interval

        if loop.variable is not None:
            result["variable"] = loop.variable

        return result if result else None

    def _format_files(self, files: list[FileConfig]) -> list[dict[str, str]]:
        """Format file configs for YAML output.

        Args:
            files: List of FileConfig objects

        Returns:
            List of file entries in YAML format
        """
        result: list[dict[str, str]] = []

        for file_config in files:
            file_dict: dict[str, str] = {
                "path": file_config.path,
                "param": file_config.param,
            }
            # Only include mime_type if explicitly set
            if file_config.mime_type:
                file_dict["mime_type"] = file_config.mime_type
            result.append(file_dict)

        return result
