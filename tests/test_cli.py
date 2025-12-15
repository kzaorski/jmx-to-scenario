"""Tests for CLI interface."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from jmx_to_scenario.cli import main


class TestCLI:
    """Tests for CLI command."""

    def test_cli_help(self) -> None:
        """Test CLI shows help."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Convert JMeter JMX file" in result.output

    def test_cli_missing_input(self) -> None:
        """Test CLI with missing input file."""
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/file.jmx"])

        assert result.exit_code != 0

    def test_cli_convert_minimal(self, temp_jmx_file: Path) -> None:
        """Test CLI converts minimal JMX."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            output_path = f.name

        result = runner.invoke(main, [str(temp_jmx_file), "--output", output_path])

        assert result.exit_code == 0
        assert "Conversion complete!" in result.output
        assert Path(output_path).exists()

        # Check YAML content
        content = Path(output_path).read_text()
        assert "name:" in content
        assert "scenario:" in content

    def test_cli_verbose_mode(self, temp_jmx_file: Path) -> None:
        """Test CLI verbose mode."""
        runner = CliRunner()

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            output_path = f.name

        result = runner.invoke(
            main, [str(temp_jmx_file), "--output", output_path, "--verbose"]
        )

        assert result.exit_code == 0
        assert "Parsing JMX file" in result.output
        assert "Building scenario" in result.output
        assert "Writing YAML file" in result.output
