# Test konwersji JMX → pt_scenario.yaml → JMX

## Cel

Zweryfikować poprawność konwersji round-trip:
1. Przekonwertować oryginalny plik JMX na format `pt_scenario.yaml`
2. Wygenerować nowy plik JMX z `pt_scenario.yaml`
3. Porównać wygenerowany JMX z oryginałem

## Narzędzia

| Narzędzie       | Lokalizacja / Użycie                                      |
|-----------------|-----------------------------------------------------------|
| jmx-to-scenario | `.venv/bin/jmx-to-scenario` (lokalny CLI)                 |
| jmeter-gen      | **MCP** (preferowane) lub CLI `/home/kzaorski/.local/bin/jmeter-gen` |

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

Porównaj `jmx/TPRM_20251024.jmx` z `generated_TPRM.jmx` pod kątem:

- **Thread Groups** - liczba wątków, ramp-up, czas trwania
- **HTTP Samplers** - metody, ścieżki, body requestów
- **JSON Extractors** - nazwy zmiennych, wyrażenia JSONPath
- **Response Assertions** - warunki asercji
- **Header Managers** - nagłówki HTTP
- **Inne elementy** - wszystko inne obecne w oryginale

### Krok 4: Raport

Zapisz wyniki porównania do pliku z datą i godziną w nazwie:
```
comparison_report_YYYYMMDD_HHMMSS.md
```
