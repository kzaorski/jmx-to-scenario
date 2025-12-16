#!/usr/bin/env python3
"""
Skrypt do porównywania plików JMX.

Użycie:
    python scripts/compare_jmx.py <original.jmx> <generated.jmx> [--output report.md]
"""

import argparse
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_jmx(path: str) -> dict:
    """Parsuje plik JMX i zwraca statystyki."""
    tree = ET.parse(path)
    root = tree.getroot()

    stats = {
        "thread_groups": [],
        "http_samplers": [],
        "json_extractors": [],
        "regex_extractors": [],
        "response_assertions": [],
        "jsonpath_assertions": [],
        "header_managers": [],
        "timers": [],
        "controllers": [],
        "other_elements": defaultdict(int),
    }

    # Thread Groups
    for tg in root.iter("ThreadGroup"):
        info = {
            "name": tg.get("testname", "Unknown"),
            "threads": "",
            "rampup": "",
            "duration": "",
            "loops": "",
        }
        for prop in tg:
            if prop.get("name") == "ThreadGroup.num_threads":
                info["threads"] = prop.text or ""
            elif prop.get("name") == "ThreadGroup.ramp_time":
                info["rampup"] = prop.text or ""
            elif prop.get("name") == "ThreadGroup.duration":
                info["duration"] = prop.text or ""
            elif prop.get("name") == "ThreadGroup.main_controller":
                for subprop in prop:
                    if subprop.get("name") == "LoopController.loops":
                        info["loops"] = subprop.text or ""
        stats["thread_groups"].append(info)

    # HTTP Samplers
    for sampler in root.iter("HTTPSamplerProxy"):
        info = {
            "name": sampler.get("testname", "Unknown"),
            "method": "",
            "path": "",
            "domain": "",
        }
        for prop in sampler:
            if prop.get("name") == "HTTPSampler.method":
                info["method"] = prop.text or ""
            elif prop.get("name") == "HTTPSampler.path":
                info["path"] = prop.text or ""
            elif prop.get("name") == "HTTPSampler.domain":
                info["domain"] = prop.text or ""
        stats["http_samplers"].append(info)

    # JSON Extractors
    for ext in root.iter("JSONPostProcessor"):
        info = {
            "name": ext.get("testname", "Unknown"),
            "variable": "",
            "jsonpath": "",
        }
        for prop in ext:
            if prop.get("name") == "JSONPostProcessor.referenceNames":
                info["variable"] = prop.text or ""
            elif prop.get("name") == "JSONPostProcessor.jsonPathExprs":
                info["jsonpath"] = prop.text or ""
        stats["json_extractors"].append(info)

    # Regex Extractors
    for ext in root.iter("RegexExtractor"):
        info = {
            "name": ext.get("testname", "Unknown"),
            "variable": "",
            "regex": "",
        }
        for prop in ext:
            if prop.get("name") == "RegexExtractor.refname":
                info["variable"] = prop.text or ""
            elif prop.get("name") == "RegexExtractor.regex":
                info["regex"] = prop.text or ""
        stats["regex_extractors"].append(info)

    # Response Assertions
    for asrt in root.iter("ResponseAssertion"):
        info = {
            "name": asrt.get("testname", "Unknown"),
            "field": "",
            "patterns": [],
        }
        for prop in asrt:
            if prop.get("name") == "Assertion.test_field":
                info["field"] = prop.text or ""
            elif prop.tag == "collectionProp":
                for pattern in prop:
                    if pattern.text:
                        info["patterns"].append(pattern.text)
        stats["response_assertions"].append(info)

    # JSONPath Assertions
    for asrt in root.iter("JSONPathAssertion"):
        info = {
            "name": asrt.get("testname", "Unknown"),
            "jsonpath": "",
            "expected": "",
        }
        for prop in asrt:
            if prop.get("name") == "JSON_PATH":
                info["jsonpath"] = prop.text or ""
            elif prop.get("name") == "EXPECTED_VALUE":
                info["expected"] = prop.text or ""
        stats["jsonpath_assertions"].append(info)

    # Header Managers
    for hm in root.iter("HeaderManager"):
        info = {"name": hm.get("testname", "Unknown"), "headers": []}
        for coll in hm.iter("collectionProp"):
            for elem in coll:
                header = {}
                for prop in elem:
                    if prop.get("name") == "Header.name":
                        header["name"] = prop.text or ""
                    elif prop.get("name") == "Header.value":
                        header["value"] = (prop.text or "")[:50]
                if header:
                    info["headers"].append(header)
        stats["header_managers"].append(info)

    # Timers
    for timer in root.iter("ConstantTimer"):
        info = {"name": timer.get("testname", "Unknown"), "delay": ""}
        for prop in timer:
            if prop.get("name") == "ConstantTimer.delay":
                info["delay"] = prop.text or ""
        stats["timers"].append(info)

    # Controllers
    controller_types = [
        "LoopController",
        "WhileController",
        "IfController",
        "TransactionController",
        "GenericController",
    ]
    for ctrl_type in controller_types:
        for ctrl in root.iter(ctrl_type):
            stats["controllers"].append(
                {"type": ctrl_type, "name": ctrl.get("testname", "Unknown")}
            )

    # Other elements
    tracked = {
        "ThreadGroup",
        "HTTPSamplerProxy",
        "JSONPostProcessor",
        "RegexExtractor",
        "ResponseAssertion",
        "JSONPathAssertion",
        "HeaderManager",
        "ConstantTimer",
        "hashTree",
        "TestPlan",
        "elementProp",
        "stringProp",
        "boolProp",
        "intProp",
        "longProp",
        "collectionProp",
        "objProp",
        "jmeterTestPlan",
        "Arguments",
        "ConfigTestElement",
        "ResultCollector",
        "TransactionController",
        "LoopController",
        "WhileController",
        "IfController",
        "GenericController",
        # ResultCollector saveConfig children (not functional, just reporting config)
        "time", "latency", "timestamp", "success", "label", "code", "message",
        "threadName", "dataType", "encoding", "assertions", "subresults",
        "responseData", "samplerData", "xml", "fieldNames", "responseHeaders",
        "requestHeaders", "responseDataOnError", "saveAssertionResultsFailureMessage",
        "bytes", "sentBytes", "url", "fileName", "hostname", "threadCounts",
        "idleTime", "connectTime", "assertionsResultsToSave",
    }
    for elem in root.iter():
        if elem.tag not in tracked:
            stats["other_elements"][elem.tag] += 1

    return stats


def compare_jmx(original: dict, generated: dict) -> dict:
    """Porównuje dwa pliki JMX."""
    comparison = {
        "summary": {},
        "thread_groups": {"original": original["thread_groups"], "generated": generated["thread_groups"]},
        "samplers": {"original": len(original["http_samplers"]), "generated": len(generated["http_samplers"])},
        "extractors": {
            "json": {"original": len(original["json_extractors"]), "generated": len(generated["json_extractors"])},
            "regex": {"original": len(original["regex_extractors"]), "generated": len(generated["regex_extractors"])},
        },
        "assertions": {
            "response": {"original": len(original["response_assertions"]), "generated": len(generated["response_assertions"])},
            "jsonpath": {"original": len(original["jsonpath_assertions"]), "generated": len(generated["jsonpath_assertions"])},
        },
        "headers": {"original": len(original["header_managers"]), "generated": len(generated["header_managers"])},
        "timers": {"original": len(original["timers"]), "generated": len(generated["timers"])},
        "controllers": {"original": len(original["controllers"]), "generated": len(generated["controllers"])},
        "other": {"original": dict(original["other_elements"]), "generated": dict(generated["other_elements"])},
    }

    # Summary
    comparison["summary"] = {
        "Thread Groups": (len(original["thread_groups"]), len(generated["thread_groups"])),
        "HTTP Samplers": (len(original["http_samplers"]), len(generated["http_samplers"])),
        "JSON Extractors": (len(original["json_extractors"]), len(generated["json_extractors"])),
        "Regex Extractors": (len(original["regex_extractors"]), len(generated["regex_extractors"])),
        "Response Assertions": (len(original["response_assertions"]), len(generated["response_assertions"])),
        "JSONPath Assertions": (len(original["jsonpath_assertions"]), len(generated["jsonpath_assertions"])),
        "Header Managers": (len(original["header_managers"]), len(generated["header_managers"])),
        "Timers": (len(original["timers"]), len(generated["timers"])),
        "Controllers": (len(original["controllers"]), len(generated["controllers"])),
    }

    return comparison


def generate_report(original_path: str, generated_path: str, original: dict, generated: dict, comparison: dict) -> str:
    """Generuje raport w formacie Markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        "# Raport porównania plików JMX",
        "",
        f"**Data:** {now}",
        f"**Plik oryginalny:** `{original_path}`",
        f"**Plik wygenerowany:** `{generated_path}`",
        "",
        "---",
        "",
        "## Podsumowanie",
        "",
        "| Element | Oryginał | Wygenerowany | Różnica |",
        "|---------|----------|--------------|---------|",
    ]

    for name, (orig, gen) in comparison["summary"].items():
        diff = gen - orig
        diff_str = f"+{diff}" if diff > 0 else str(diff)
        lines.append(f"| {name} | {orig} | {gen} | {diff_str} |")

    lines.extend(["", "---", "", "## Thread Groups", ""])

    # Thread Groups comparison
    lines.append("### Oryginał")
    for tg in original["thread_groups"]:
        lines.append(f"- **{tg['name']}**: threads={tg['threads']}, rampup={tg['rampup']}, duration={tg['duration']}, loops={tg['loops']}")

    lines.append("")
    lines.append("### Wygenerowany")
    for tg in generated["thread_groups"]:
        lines.append(f"- **{tg['name']}**: threads={tg['threads']}, rampup={tg['rampup']}, duration={tg['duration']}, loops={tg['loops']}")

    # HTTP Samplers
    lines.extend(["", "---", "", "## HTTP Samplers", ""])
    lines.append(f"**Oryginał:** {len(original['http_samplers'])} samplerów")
    lines.append(f"**Wygenerowany:** {len(generated['http_samplers'])} samplerów")
    lines.append("")

    # Compare sampler names
    orig_names = {s["name"] for s in original["http_samplers"]}
    gen_names = {s["name"].lstrip("[0-9] ") for s in generated["http_samplers"]}
    # Normalize generated names (remove [N] prefix)
    gen_names_normalized = set()
    for s in generated["http_samplers"]:
        name = s["name"]
        if name.startswith("[") and "] " in name:
            name = name.split("] ", 1)[1]
        gen_names_normalized.add(name)

    missing = orig_names - gen_names_normalized
    if missing:
        lines.append("**Brakujące w wygenerowanym:**")
        for name in sorted(missing):
            lines.append(f"- {name}")

    # JSON Extractors
    lines.extend(["", "---", "", "## JSON Extractors", ""])
    lines.append("### Oryginał")
    for ext in original["json_extractors"]:
        lines.append(f"- `{ext['variable']}` = `{ext['jsonpath']}`")

    lines.append("")
    lines.append("### Wygenerowany")
    for ext in generated["json_extractors"]:
        lines.append(f"- `{ext['variable']}` = `{ext['jsonpath']}`")

    # Other elements
    orig_other = comparison["other"]["original"]
    gen_other = comparison["other"]["generated"]
    if orig_other:
        lines.extend(["", "---", "", "## Inne elementy (nieprzeniesione)", ""])
        lines.append("| Element | Oryginał | Wygenerowany |")
        lines.append("|---------|----------|--------------|")
        all_tags = set(orig_other.keys()) | set(gen_other.keys())
        for tag in sorted(all_tags):
            orig_count = orig_other.get(tag, 0)
            gen_count = gen_other.get(tag, 0)
            if orig_count != gen_count:
                lines.append(f"| {tag} | {orig_count} | {gen_count} |")

    # Summary
    total_orig = sum(v[0] for v in comparison["summary"].values())
    total_gen = sum(v[1] for v in comparison["summary"].values())
    if total_orig > 0:
        compatibility = (total_gen / total_orig) * 100
    else:
        compatibility = 100

    lines.extend([
        "",
        "---",
        "",
        "## Ocena",
        "",
        f"**Zgodność:** {compatibility:.1f}%",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Porównuje dwa pliki JMX")
    parser.add_argument("original", help="Ścieżka do oryginalnego pliku JMX")
    parser.add_argument("generated", help="Ścieżka do wygenerowanego pliku JMX")
    parser.add_argument("--output", "-o", help="Ścieżka do pliku raportu (domyślnie: stdout)")
    args = parser.parse_args()

    # Parse both files
    print(f"Parsowanie: {args.original}")
    original = parse_jmx(args.original)

    print(f"Parsowanie: {args.generated}")
    generated = parse_jmx(args.generated)

    # Compare
    print("Porównywanie...")
    comparison = compare_jmx(original, generated)

    # Generate report
    report = generate_report(args.original, args.generated, original, generated, comparison)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"Raport zapisany: {args.output}")
    else:
        print("\n" + report)


if __name__ == "__main__":
    main()
