# JMX to pt_scenario.yaml Converter - Implementation Plan

## Overview
Build a Python CLI tool to convert JMeter JMX files (XML) to pt_scenario.yaml format based on SPEC.md.

**User Preferences:**
- Python 3.12+
- src layout with pyproject.toml
- Click CLI framework
- Minimal tests only

**Development Resources:**
- Real JMX samples available in `jmx/` folder (confidential - do not reference filenames)
- Use these for manual testing and development validation

---

## Project Structure

```
jmx-to-scenario/
├── pyproject.toml
├── .gitignore                        # Exclude jmx/ folder
├── SPEC.md                           # Already exists
├── jmx/                              # Real JMX samples (confidential, gitignored)
│   └── *.jmx
├── src/
│   └── jmx_to_scenario/
│       ├── __init__.py               # Package metadata + exports
│       ├── cli.py                    # Click CLI interface
│       ├── exceptions.py             # Custom exceptions
│       └── core/
│           ├── __init__.py
│           ├── data_types.py         # Dataclasses (Section 6 of spec)
│           ├── jmx_parser.py         # JMX XML parsing logic
│           ├── scenario_builder.py   # pt_scenario construction
│           ├── yaml_writer.py        # YAML output formatting
│           └── converters/
│               ├── __init__.py
│               ├── groovy_converter.py   # Groovy to JSONPath
│               └── helpers.py            # XML property helpers
└── tests/
    ├── conftest.py
    ├── test_cli.py
    └── test_jmx_parser.py
```

---

## Dependencies (pyproject.toml)

```toml
[project]
name = "jmx-to-scenario"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "click>=8.1.0",
    "pyyaml>=6.0",
    "defusedxml>=0.7.1",   # Secure XML parsing for untrusted JMX
]

[project.optional-dependencies]
dev = ["pytest>=7.4.0", "ruff>=0.1.0"]

[project.scripts]
jmx-to-scenario = "jmx_to_scenario.cli:main"
```

---

## Implementation Order

### Phase 1: Foundation
1. **pyproject.toml** - Project configuration
2. **exceptions.py** - `JMXParseException`, `ConversionException`, `OutputException`
3. **core/data_types.py** - All dataclasses from SPEC.md Section 6:
   - `JMXDefaults`, `CaptureConfig`, `AssertConfig`, `LoopConfig`
   - `ExtractedSampler`, `ScenarioSettings`, `ScenarioStep`
   - `ParsedScenario`, `ImportResult`
4. **core/converters/helpers.py** - `get_string_prop()`, `get_bool_prop()`, `get_int_prop()`

### Phase 2: JMX Parsing
5. **core/jmx_parser.py** - `JMXParser` class:
   - `_build_hash_tree_map()` - Critical HashTree algorithm
   - `_extract_test_plan_name()` - TestPlan parsing
   - `_extract_http_defaults()` - ConfigTestElement parsing
   - `_extract_user_variables()` - Arguments parsing
   - `_extract_thread_settings()` - ThreadGroup parsing

### Phase 3: HTTP Sampler Extraction
6. Continue **jmx_parser.py**:
   - `_extract_samplers()` - Find all HTTPSamplerProxy
   - `_extract_sampler_data()` - Method, path, enabled
   - `_extract_request_body()` - Raw body vs form params
   - `_extract_headers()` - HeaderManager
   - `_extract_captures()` - JSONPostProcessor
   - `_extract_assertions()` - ResponseAssertion, JSONPathAssertion
   - `_extract_timers()` - ConstantTimer, UniformRandomTimer

### Phase 4: Controllers & Converters
7. **core/converters/groovy_converter.py** - `convert_groovy_to_jsonpath()`
8. Continue **jmx_parser.py**:
   - `_extract_loop_config()` - LoopController, WhileController

### Phase 5: Output
9. **core/scenario_builder.py** - `ScenarioBuilder.build()`
10. **core/yaml_writer.py** - `YAMLWriter.write()`

### Phase 6: CLI & Integration
11. **cli.py** - Click command with options
12. **__init__.py** files - Exports
13. **tests/** - Minimal test suite

---

## Key Algorithms

### HashTree Parsing (from SPEC.md Section 5.1)
```python
def _process_hash_tree(self, tree: ET.Element) -> None:
    children = list(tree)
    i = 0
    while i < len(children):
        child = children[i]
        if child.tag != 'hashTree':
            self._element_children[child] = []
            if i + 1 < len(children) and children[i + 1].tag == 'hashTree':
                child_tree = children[i + 1]
                for grandchild in child_tree:
                    if grandchild.tag != 'hashTree':
                        self._element_children[child].append(grandchild)
                self._process_hash_tree(child_tree)
            i += 2
        else:
            i += 1
```

### HTTP Defaults Inheritance
- Sampler domain/port/protocol override defaults only if non-empty
- Build base_url: `{protocol}://{domain}:{port}` (omit default ports)

### Request Body Extraction
- If `postBodyRaw=true`: Parse `Argument.value` as JSON payload
- If `postBodyRaw=false`: Extract as query/form params dict

---

## CLI Interface

```bash
jmx-to-scenario <input.jmx> [--output <output.yaml>] [--verbose]
```

Exit codes: 0=success, 1=parse error, 2=conversion error, 3=I/O error

---

## Error Handling

- **Fatal errors**: Raise exceptions, exit with code
- **Warnings** (collected in ImportResult.warnings):
  - "TransactionController ignored (not supported)"
  - "Multiple ThreadGroups found, using first only"
  - "Could not convert Groovy expression: {expr}"
  - "match_numbers=N converted to 'first' (N-th not supported)"
  - "JSR223Sampler ignored (Groovy scripts not portable)"

---

## Additional Considerations (from real JMX analysis)

### HTML Entity Decoding
Real JMX files use XML entities in body content:
- `&quot;` → `"`
- `&#xd;` → carriage return (strip or normalize)
- `&apos;` → `'`

Python's `xml.etree` handles this automatically when parsing.

### Empty Properties
Handle empty `match_numbers` in JSONPostProcessor (default to "first").

### Disabled Samplers
Preserve `enabled="false"` in output as `enabled: false`.

### Unsupported Elements (skip with warning)
- `JSR223Sampler` - Groovy/JavaScript scripts not portable
- `BeanShellSampler` - BeanShell scripts not portable
- `RegexExtractor` - Regex not in pt_scenario spec
- `CSVDataSetConfig` - External data sources

---

## Files to Create

| File | Purpose |
|------|---------|
| `.gitignore` | Exclude jmx/ folder and Python artifacts |
| `pyproject.toml` | Project config |
| `src/jmx_to_scenario/__init__.py` | Package exports |
| `src/jmx_to_scenario/cli.py` | CLI entry point |
| `src/jmx_to_scenario/exceptions.py` | Exception classes |
| `src/jmx_to_scenario/core/__init__.py` | Core exports |
| `src/jmx_to_scenario/core/data_types.py` | Dataclasses |
| `src/jmx_to_scenario/core/jmx_parser.py` | Main parsing logic |
| `src/jmx_to_scenario/core/scenario_builder.py` | Build scenario |
| `src/jmx_to_scenario/core/yaml_writer.py` | YAML output |
| `src/jmx_to_scenario/core/converters/__init__.py` | Converter exports |
| `src/jmx_to_scenario/core/converters/helpers.py` | XML utilities |
| `src/jmx_to_scenario/core/converters/groovy_converter.py` | Groovy conversion |
| `tests/conftest.py` | Test fixtures (inline XML strings) |
| `tests/test_cli.py` | CLI tests |
| `tests/test_jmx_parser.py` | Parser tests |

**Testing approach**: Use inline XML strings in tests, not the confidential JMX files. Manual testing with real JMX files from `jmx/` folder.

---

## Reference
- SPEC.md contains complete algorithms, data structures, and example conversions
- Section 5: Parsing algorithms with Python pseudocode
- Section 6: All dataclass definitions
- Section 7: Implementation guide
- Section 10: Example JMX to YAML conversions
- **PT_SCENARIO_RULES.md** - Complete pt_scenario.yaml format guide

---

## pt_scenario.yaml Format Updates (from PT_SCENARIO_RULES.md)

### Required Fields
- Root: `name`, `scenario` (version is optional)
- Step: `name`, `endpoint`

### Loop Syntax (updated)
```yaml
loop:
  count: 5              # Fixed count
  # OR
  foreach: "varName"    # Iterate array
  # OR
  while: "${status} != 'completed'"  # Condition
  max: 100              # Safety limit
  variable: "i"         # Loop variable name
  interval: 30000       # Wait between iterations (ms)
```

### think_time
**Decision**: Keep `think_time` (per user). Convert JMX timers to `step.think_time` in milliseconds.

### Endpoint Formats
1. **operationId** (preferred): `endpoint: "createUser"`
2. **METHOD /path**: `endpoint: "POST /users"`
