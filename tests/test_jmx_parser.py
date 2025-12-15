"""Tests for JMX parser."""

from pathlib import Path

import pytest

from jmx_to_scenario.core.jmx_parser import JMXParser


class TestJMXParser:
    """Tests for JMXParser class."""

    def test_parse_minimal_jmx(self, temp_jmx_file: Path) -> None:
        """Test parsing a minimal JMX file."""
        parser = JMXParser()
        result = parser.parse(str(temp_jmx_file))

        assert result.success
        assert result.scenario is not None
        assert result.scenario.name == "Test Plan"

    def test_parse_samplers(self, temp_jmx_file: Path) -> None:
        """Test extracting samplers from JMX."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file))

        assert len(samplers) == 1
        sampler = samplers[0]
        assert sampler.name == "GET /api/test"
        assert sampler.method == "GET"
        assert sampler.path == "/api/test"
        assert sampler.domain == "example.com"
        assert sampler.protocol == "https"

    def test_parse_with_capture(self, temp_jmx_file_with_capture: Path) -> None:
        """Test parsing JMX with JSONPostProcessor."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_capture))

        assert len(samplers) == 1
        sampler = samplers[0]
        assert sampler.name == "Create User"
        assert sampler.method == "POST"
        assert len(sampler.captures) == 1

        capture = sampler.captures[0]
        assert capture.variable_name == "userId"
        assert capture.jsonpath == "$.id"
        assert capture.match == "first"

    def test_parse_with_payload(self, temp_jmx_file_with_capture: Path) -> None:
        """Test parsing JMX with request body."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_capture))

        sampler = samplers[0]
        assert sampler.payload == {"name": "test"}

    def test_parse_nonexistent_file(self) -> None:
        """Test parsing a nonexistent file raises exception."""
        parser = JMXParser()

        with pytest.raises(Exception):
            parser.parse("/nonexistent/file.jmx")

    def test_warnings_collected(self, temp_jmx_file: Path) -> None:
        """Test that warnings are collected during parsing."""
        parser = JMXParser()
        parser.parse(str(temp_jmx_file))

        # No warnings expected for minimal JMX
        warnings = parser.get_warnings()
        assert isinstance(warnings, list)
