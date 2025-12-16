# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JMX to Scenario Converter - A Python CLI tool that converts JMeter JMX test plan files to `pt_scenario.yaml` format. This enables migration from JMeter GUI-based test development to YAML-based workflows.

## Build and Development Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run the converter
jmx-to-scenario <input.jmx> [--output <output.yaml>] [--verbose]

# Run tests
pytest

# Run a single test
pytest tests/test_jmx_parser.py::TestJMXParser::test_parse_minimal_jmx

# Lint code
ruff check .
ruff format .
```

## Architecture

The converter follows a three-stage pipeline:

1. **JMXParser** (`src/jmx_to_scenario/core/jmx_parser.py`) - Parses JMX XML using `defusedxml`, builds a hashTree hierarchy map, and extracts samplers into `ExtractedSampler` dataclasses
2. **ScenarioBuilder** (`src/jmx_to_scenario/core/scenario_builder.py`) - Converts extracted samplers to `ScenarioStep` objects with proper YAML formatting for captures and assertions
3. **YAMLWriter** (`src/jmx_to_scenario/core/yaml_writer.py`) - Serializes `ParsedScenario` to pt_scenario.yaml format

### Key Data Flow

```
JMX File → JMXParser.parse() → ImportResult (scenario metadata)
         → JMXParser.parse_samplers() → list[ExtractedSampler]
         → ScenarioBuilder.build() → ParsedScenario
         → YAMLWriter.write() → YAML file
```

### JMX HashTree Structure

JMX files use `<hashTree>` elements to define parent-child relationships. The parser builds an `_element_children` map by pairing each element with the following hashTree's contents. This is critical for finding sampler children (captures, assertions, headers, timers).

## Key Files

- `src/jmx_to_scenario/core/data_types.py` - All dataclasses (`ExtractedSampler`, `ScenarioStep`, `CaptureConfig`, etc.)
- `src/jmx_to_scenario/core/converters/helpers.py` - XML property extraction helpers (`get_string_prop`, `get_bool_prop`, etc.)
- `src/jmx_to_scenario/core/converters/groovy_converter.py` - Groovy condition to JSONPath conversion
- `SPEC.md` - Complete technical specification for JMX to pt_scenario mapping
- `PT_SCENARIO_RULES.md` - Reference for valid pt_scenario.yaml structure

## Testing

Tests use pytest fixtures in `tests/conftest.py` that provide JMX content strings. Create temp files with `tempfile.NamedTemporaryFile` for parser tests.
