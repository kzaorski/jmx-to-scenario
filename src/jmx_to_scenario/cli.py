"""CLI interface for JMX to pt_scenario.yaml converter."""

import sys
from pathlib import Path

import click

from jmx_to_scenario.core.jmx_parser import JMXParser
from jmx_to_scenario.core.scenario_builder import ScenarioBuilder
from jmx_to_scenario.core.yaml_writer import YAMLWriter
from jmx_to_scenario.exceptions import (
    ConversionException,
    JMXParseException,
    OutputException,
)

# Exit codes
EXIT_SUCCESS = 0
EXIT_PARSE_ERROR = 1
EXIT_CONVERSION_ERROR = 2
EXIT_IO_ERROR = 3


@click.command()
@click.argument("input_jmx", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False),
    default="pt_scenario.yaml",
    help="Output YAML file path (default: pt_scenario.yaml)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed output",
)
def main(input_jmx: str, output: str, verbose: bool) -> None:
    """Convert JMeter JMX file to pt_scenario.yaml format.

    INPUT_JMX is the path to the JMeter test plan file (.jmx).
    """
    click.echo("JMX to pt_scenario.yaml Converter")
    click.echo()

    input_path = Path(input_jmx)
    output_path = Path(output)

    click.echo(f"Input:  {input_path}")
    click.echo(f"Output: {output_path}")
    click.echo()

    try:
        # Parse JMX file
        if verbose:
            click.echo("Parsing JMX file...")

        parser = JMXParser()
        result = parser.parse(str(input_path))
        samplers = parser.parse_samplers(str(input_path))

        if not result.success or result.scenario is None:
            click.secho("Error: Failed to parse JMX file", fg="red")
            for error in result.errors:
                click.secho(f"  - {error}", fg="red")
            sys.exit(EXIT_PARSE_ERROR)

        # Build scenario
        if verbose:
            click.echo("Building scenario...")

        builder = ScenarioBuilder()
        scenario = builder.build(
            name=result.scenario.name,
            samplers=samplers,
            settings=result.scenario.settings,
            variables=result.scenario.variables,
            description=result.scenario.description,
        )

        # Collect all warnings
        all_warnings = (
            parser.get_warnings() + builder.get_warnings() + result.warnings
        )

        # Write YAML
        if verbose:
            click.echo("Writing YAML file...")

        writer = YAMLWriter()
        writer.write(scenario, str(output_path))

        # Show summary
        click.echo("Extracted:")
        click.echo(f"  - Scenario name: {scenario.name}")
        if scenario.settings.base_url:
            click.echo(f"  - Base URL: {scenario.settings.base_url}")
        click.echo(f"  - Variables: {len(scenario.variables)}")
        click.echo(f"  - Steps: {len(scenario.steps)}")

        # Count captures and assertions
        capture_count = sum(len(step.capture) for step in scenario.steps)
        assert_count = sum(1 for step in scenario.steps if step.assert_config)
        click.echo(f"  - Captures: {capture_count}")
        click.echo(f"  - Assertions: {assert_count}")
        click.echo()

        # Show warnings
        if all_warnings:
            click.secho("Warnings:", fg="yellow")
            for warning in all_warnings:
                click.secho(f"  - {warning}", fg="yellow")
            click.echo()

        click.secho("Conversion complete!", fg="green")
        sys.exit(EXIT_SUCCESS)

    except JMXParseException as e:
        click.secho(f"Parse error: {e}", fg="red")
        sys.exit(EXIT_PARSE_ERROR)

    except ConversionException as e:
        click.secho(f"Conversion error: {e}", fg="red")
        sys.exit(EXIT_CONVERSION_ERROR)

    except OutputException as e:
        click.secho(f"Output error: {e}", fg="red")
        sys.exit(EXIT_IO_ERROR)

    except Exception as e:
        click.secho(f"Unexpected error: {e}", fg="red")
        if verbose:
            import traceback

            click.echo(traceback.format_exc())
        sys.exit(EXIT_CONVERSION_ERROR)


if __name__ == "__main__":
    main()
