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


class TestFileExtraction:
    """Tests for file upload extraction from JMX."""

    def test_extract_single_file(self, temp_jmx_file_with_file_upload: Path) -> None:
        """Test extracting single file upload from JMX."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_file_upload))

        assert len(samplers) == 1
        sampler = samplers[0]
        assert sampler.name == "Upload File"
        assert len(sampler.files) == 1

        file_config = sampler.files[0]
        assert file_config.path == "document.pdf"
        assert file_config.param == "file"
        assert file_config.mime_type == "application/pdf"

    def test_extract_multiple_files(self, temp_jmx_file_with_multiple_files: Path) -> None:
        """Test extracting multiple file uploads from JMX."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_multiple_files))

        assert len(samplers) == 1
        sampler = samplers[0]
        assert len(sampler.files) == 2

        # First file
        file1 = sampler.files[0]
        assert file1.path == "reports/report.pdf"
        assert file1.param == "document"
        assert file1.mime_type == "application/pdf"

        # Second file with JMeter variable
        file2 = sampler.files[1]
        assert file2.path == "${image_path}"
        assert file2.param == "image"
        assert file2.mime_type == "image/png"

    def test_extract_no_files(self, temp_jmx_file: Path) -> None:
        """Test sampler without file uploads returns empty list."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file))

        assert len(samplers) == 1
        sampler = samplers[0]
        assert sampler.files == []


class TestControllerHandling:
    """Tests for JMX controller element handling."""

    def test_random_controller_marks_samplers(
        self, temp_jmx_file_with_random_controller: Path
    ) -> None:
        """Test RandomController sets random=True on child samplers."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_random_controller))

        assert len(samplers) == 2
        assert all(s.random for s in samplers)
        assert samplers[0].name == "Option A"
        assert samplers[1].name == "Option B"

    def test_test_action_applies_think_time(
        self, temp_jmx_file_with_test_action: Path
    ) -> None:
        """Test TestAction PAUSE applies think_time to next sampler."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_test_action))

        assert len(samplers) == 2
        assert samplers[0].think_time is None  # First has no preceding TestAction
        assert samplers[1].think_time == 2000  # Second has TestAction before it

    def test_transaction_controller_prefixes_names(
        self, temp_jmx_file_with_transaction_controller: Path
    ) -> None:
        """Test TransactionController prefixes child sampler names."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file_with_transaction_controller))

        assert len(samplers) == 2
        assert samplers[0].name == "Login Flow: Get Login Page"
        assert samplers[1].name == "Login Flow: Submit Login"

    def test_sampler_without_controllers_has_no_random_flag(
        self, temp_jmx_file: Path
    ) -> None:
        """Test samplers outside controllers have random=False."""
        parser = JMXParser()
        samplers = parser.parse_samplers(str(temp_jmx_file))

        assert len(samplers) == 1
        assert samplers[0].random is False
