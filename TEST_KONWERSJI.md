# Test konwersji JMX → pt_scenario.yaml → JMX

## Cel

Zweryfikować poprawność konwersji round-trip:
1. Przekonwertować oryginalny plik JMX na format `pt_scenario.yaml`
2. Wygenerować nowy plik JMX z `pt_scenario.yaml`
3. Porównać wygenerowany JMX z oryginałem

## Narzędzia

| Narzędzie       | Opis                                      |
|-----------------|-------------------------------------------|
| jmx-to-scenario | Konwersja JMX → pt_scenario.yaml          |
| jmeter-gen      | Generowanie JMX z pt_scenario.yaml        |
| compare_jmx.py  | Porównywanie plików JMX                   |

### jmx-to-scenario

Konwertuje plik JMX do formatu pt_scenario.yaml.

```bash
# Instalacja (w katalogu jmx-to-scenario)
pip install -e ".[dev]"

# Użycie
jmx-to-scenario <input.jmx> [--output <output.yaml>] [--verbose]

# Przykład
.venv/bin/jmx-to-scenario jmx/TPRM_20251024.jmx -o pt_scenario.yaml -v
```

Opcje:
- `-o`, `--output` - ścieżka do pliku wyjściowego (domyślnie: pt_scenario.yaml)
- `-v`, `--verbose` - szczegółowe logi

### jmeter-gen

Generuje i waliduje pliki JMX.

```bash
# Instalacja (w katalogu jmeter-test-generator)
pip install -e ".[dev]"

# Generowanie JMX z pt_scenario.yaml (sekwencyjne requesty)
jmeter-gen generate --scenario pt_scenario.yaml --spec minimal_openapi.yaml --output generated_TPRM.jmx

# Generowanie JMX z OpenAPI (równoległe requesty)
jmeter-gen generate --spec openapi.yaml --output test.jmx

# Walidacja scenariusza
jmeter-gen validate scenario pt_scenario.yaml --spec minimal_openapi.yaml

# Walidacja wygenerowanego JMX
jmeter-gen validate script generated_TPRM.jmx
```

**Minimalny plik OpenAPI** (jeśli brak specyfikacji):
```yaml
# minimal_openapi.yaml
openapi: 3.0.0
info:
  title: API
  version: 1.0.0
servers:
  - url: https://example.com
paths: {}
```

### compare_jmx.py

Porównuje dwa pliki JMX i generuje raport.

```bash
# Użycie
python3 scripts/compare_jmx.py <original.jmx> <generated.jmx> [-o report.md]

# Przykład
python3 scripts/compare_jmx.py jmx/TPRM_20251024.jmx generated_TPRM.jmx -o comparison_report.md
```

Opcje:
- `-o`, `--output` - zapisz raport do pliku (domyślnie: wyświetl na stdout)

## Pliki

| Plik                    | Opis                            |
|-------------------------|---------------------------------|
| `jmx/TPRM_20251024.jmx` | Oryginalny plik JMX (wejście). Plik jest duży, wczytaj go kawałkami.   |
| `pt_scenario.yaml`      | Wynik konwersji jmx-to-scenario |
| `generated_TPRM.jmx`    | Wygenerowany JMX (do porównania)|

## Kroki

### Krok 0: Przygotowanie

Usuń stare pliki wynikowe:
```bash
rm -f pt_scenario.yaml generated_TPRM.jmx
```

### Krok 1: Konwersja JMX → pt_scenario.yaml

```bash
.venv/bin/jmx-to-scenario jmx/TPRM_20251024.jmx -o pt_scenario.yaml -v
```

### Krok 2: Generowanie JMX z pt_scenario.yaml

Użyj **MCP jmeter-gen** (preferowane):
- Narzędzie `generate_scenario_jmx` wymaga `pt_scenario.yaml` oraz specyfikacji OpenAPI
- Jeśli spec nie istnieje, utwórz minimalny plik OpenAPI na podstawie oryginalnego JMX

Alternatywnie CLI:
```bash
jmeter-gen generate --output generated_TPRM.jmx
```

### Krok 3: Porównanie plików JMX

Użyj skryptu `compare_jmx.py`:
```bash
python3 scripts/compare_jmx.py jmx/TPRM_20251024.jmx generated_TPRM.jmx -o comparison_report.md
```

Skrypt porównuje:
- **Thread Groups** - liczba wątków, ramp-up, czas trwania
- **HTTP Samplers** - metody, ścieżki, body requestów
- **JSON Extractors** - nazwy zmiennych, wyrażenia JSONPath
- **Regex Extractors** - wyrażenia regularne
- **Response Assertions** - warunki asercji
- **JSONPath Assertions** - asercje JSONPath
- **Header Managers** - nagłówki HTTP
- **Timers** - opóźnienia
- **Controllers** - kontrolery (Loop, While, If, Transaction)
- **Inne elementy** - wszystko inne obecne w oryginale

Opcje:
- `-o FILE` / `--output FILE` - zapisz raport do pliku (domyślnie: stdout)

### Krok 4: Raport

Zapisz wyniki porównania do pliku z datą i godziną w nazwie:
```
comparison_report_YYYYMMDD_HHMMSS.md
```
