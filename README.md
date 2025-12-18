# JMX to Scenario Converter

> **Note**: This tool is currently in development and intended for personal use only. Use at your own risk.

A Python CLI tool that converts JMeter JMX test plan files to `pt_scenario.yaml` format.

## Companion Tool

This is a companion tool to [jmeter-gen](https://github.com/kzaorski/jmeter-gen). It enables migration of existing JMeter JMX test plans to the YAML-based workflow used by jmeter-gen.

**Workflow:**
1. Export your existing JMeter test plan as `.jmx`
2. Convert it to `pt_scenario.yaml` using this tool
3. Use the scenario with `jmeter-gen` to generate new JMX files or modify the test flow

## Features

- Converts HTTP requests (samplers) to scenario steps
- Extracts variable captures (JSONPostProcessor)
- Preserves headers, assertions, and timers
- Supports loop controllers and while conditions
- Maintains user-defined variables
- Extracts thread group settings (threads, rampup, duration)

## Installation

Requires Python 3.11+

```bash
# Clone the repository
git clone https://github.com/kzaorski/jmx-to-scenario.git
cd jmx-to-scenario

# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Basic conversion
jmx-to-scenario input.jmx

# Specify output file
jmx-to-scenario input.jmx --output my_scenario.yaml

# Verbose output
jmx-to-scenario input.jmx --verbose
```

## Supported JMX Elements

| Element | Support |
|---------|---------|
| TestPlan | Full |
| ThreadGroup | Full |
| HTTPSamplerProxy | Full |
| ConfigTestElement (HTTP Defaults) | Full |
| Arguments (User Variables) | Full |
| JSONPostProcessor | Full |
| HeaderManager | Full |
| ResponseAssertion | Partial (status code) |
| JSONPathAssertion | Full |
| ConstantTimer | Full |
| UniformRandomTimer | Partial (average) |
| LoopController | Full |
| WhileController | Partial |

## Architecture

The converter follows a three-stage pipeline:

```
JMX File → JMXParser → ScenarioBuilder → YAMLWriter → pt_scenario.yaml
```

1. **JMXParser** - Parses JMX XML, builds hashTree hierarchy, extracts samplers
2. **ScenarioBuilder** - Converts extracted data to scenario steps
3. **YAMLWriter** - Serializes to pt_scenario.yaml format

## Development

```bash
# Run tests
pytest

# Run single test
pytest tests/test_jmx_parser.py::TestJMXParser::test_parse_minimal_jmx

# Lint code
ruff check .
ruff format .
```

## License

MIT
