"""JMX file parser for converting to pt_scenario format."""

import json
from xml.etree.ElementTree import Element

import defusedxml.ElementTree as ET

from jmx_to_scenario.core.converters.groovy_converter import (
    convert_groovy_to_condition,
    convert_match_number,
)
from jmx_to_scenario.core.converters.helpers import (
    get_attribute,
    get_bool_prop,
    get_int_prop,
    get_string_prop,
    is_enabled,
    normalize_variable_refs,
    strip_carriage_returns,
)
from jmx_to_scenario.core.data_types import (
    AssertConfig,
    CaptureConfig,
    ExtractedSampler,
    FileConfig,
    ImportResult,
    JMXDefaults,
    LoopConfig,
    ParsedScenario,
    ParsingContext,
    ScenarioSettings,
)
from jmx_to_scenario.exceptions import JMXParseException


class JMXParser:
    """Parse JMeter JMX files into intermediate representations."""

    # Supported sampler types
    SUPPORTED_SAMPLERS = {"HTTPSamplerProxy"}

    # Elements to skip with warning
    UNSUPPORTED_ELEMENTS = {
        "JSR223Sampler": "Groovy/JavaScript scripts not portable",
        "BeanShellSampler": "BeanShell scripts not portable",
        "RegexExtractor": "Regex extraction not supported in pt_scenario",
        "CSVDataSetConfig": "External data sources not supported",
    }

    # Controller elements that affect child samplers' context
    CONTEXT_CONTROLLERS = {"RandomController", "TransactionController"}

    def __init__(self) -> None:
        self._root: Element | None = None
        self._element_children: dict[Element, list[Element]] = {}
        self._defaults: JMXDefaults = JMXDefaults()
        self._warnings: list[str] = []
        self._errors: list[str] = []
        self._global_headers: dict[str, str] = {}

    def parse(self, jmx_path: str) -> ImportResult:
        """Parse JMX file and return import result.

        Args:
            jmx_path: Path to JMX file

        Returns:
            ImportResult with parsed scenario or errors
        """
        self._warnings = []
        self._errors = []

        try:
            self._root = self._parse_jmx(jmx_path)
            self._build_hash_tree_map()

            # Extract global configuration
            name = self._extract_test_plan_name()
            self._defaults = self._extract_http_defaults()
            variables = self._extract_user_variables()
            settings = self._extract_thread_settings()
            self._global_headers = self._extract_global_headers()

            # Build base URL from defaults
            if self._defaults.domain:
                settings.base_url = self._build_base_url(
                    self._defaults.domain,
                    self._defaults.port,
                    self._defaults.protocol,
                )

            # Extract samplers
            samplers = self._extract_samplers()

            # Build scenario
            scenario = ParsedScenario(
                name=name,
                settings=settings,
                variables=variables,
                steps=[],  # Steps will be built by ScenarioBuilder
            )

            return ImportResult(
                success=True,
                scenario=scenario,
                warnings=self._warnings,
                errors=self._errors,
                # Store samplers for ScenarioBuilder access
            )

        except JMXParseException:
            raise
        except Exception as e:
            self._errors.append(str(e))
            return ImportResult(
                success=False,
                warnings=self._warnings,
                errors=self._errors,
            )

    def parse_samplers(self, jmx_path: str) -> list[ExtractedSampler]:
        """Parse JMX file and return extracted samplers.

        This is the main method for getting samplers for scenario building.

        Args:
            jmx_path: Path to JMX file

        Returns:
            List of ExtractedSampler objects
        """
        self._warnings = []
        self._errors = []

        self._root = self._parse_jmx(jmx_path)
        self._build_hash_tree_map()

        # Extract global configuration
        self._defaults = self._extract_http_defaults()
        self._global_headers = self._extract_global_headers()

        return self._extract_samplers()

    def get_warnings(self) -> list[str]:
        """Get accumulated warnings."""
        return self._warnings

    def get_errors(self) -> list[str]:
        """Get accumulated errors."""
        return self._errors

    def _parse_jmx(self, jmx_path: str) -> Element:
        """Parse JMX XML file with security protections.

        Args:
            jmx_path: Path to JMX file

        Returns:
            Root element of parsed XML

        Raises:
            JMXParseException: If parsing fails
        """
        try:
            tree = ET.parse(jmx_path)
            return tree.getroot()
        except ET.ParseError as e:
            raise JMXParseException("Invalid XML", str(e)) from e
        except FileNotFoundError as e:
            raise JMXParseException("File not found", jmx_path) from e

    def _build_hash_tree_map(self) -> None:
        """Build element-children map from JMX hashTree structure.

        JMX uses hashTree elements to define parent-child relationships.
        Each element is followed by a hashTree containing its children.
        """
        if self._root is None:
            return

        main_tree = self._root.find("hashTree")
        if main_tree is not None:
            self._process_hash_tree(main_tree)

    def _process_hash_tree(self, tree: Element) -> None:
        """Process hashTree recursively to build parent-child map.

        Args:
            tree: hashTree element to process
        """
        children = list(tree)
        i = 0
        while i < len(children):
            child = children[i]
            if child.tag != "hashTree":
                self._element_children[child] = []
                if i + 1 < len(children) and children[i + 1].tag == "hashTree":
                    child_tree = children[i + 1]
                    for grandchild in child_tree:
                        if grandchild.tag != "hashTree":
                            self._element_children[child].append(grandchild)
                    self._process_hash_tree(child_tree)
                i += 2
            else:
                i += 1

    def _get_children(self, element: Element) -> list[Element]:
        """Get direct children of an element from the hashTree map.

        Args:
            element: Parent element

        Returns:
            List of child elements
        """
        return self._element_children.get(element, [])

    def _extract_test_plan_name(self) -> str:
        """Extract scenario name from TestPlan element.

        Returns:
            Test plan name or default
        """
        if self._root is None:
            return "Converted Test Plan"

        test_plan = self._root.find(".//TestPlan")
        if test_plan is not None:
            return get_attribute(test_plan, "testname", "Converted Test Plan")

        return "Converted Test Plan"

    def _extract_http_defaults(self) -> JMXDefaults:
        """Extract HTTP Request Defaults from ConfigTestElement.

        Returns:
            JMXDefaults with extracted values
        """
        defaults = JMXDefaults()

        if self._root is None:
            return defaults

        # Find ConfigTestElement with HttpDefaultsGui
        for config in self._root.iter("ConfigTestElement"):
            gui_class = config.get("guiclass", "")
            if "HttpDefaultsGui" in gui_class:
                defaults.domain = get_string_prop(config, "HTTPSampler.domain")
                defaults.port = get_string_prop(config, "HTTPSampler.port")
                defaults.protocol = get_string_prop(config, "HTTPSampler.protocol", "http")
                defaults.content_encoding = get_string_prop(
                    config, "HTTPSampler.contentEncoding", "UTF-8"
                )
                break

        return defaults

    def _extract_user_variables(self) -> dict[str, str]:
        """Extract User Defined Variables from Arguments element.

        Returns:
            Dictionary of variable name to value
        """
        variables: dict[str, str] = {}

        if self._root is None:
            return variables

        # Find Arguments elements (User Defined Variables)
        for args in self._root.iter("Arguments"):
            gui_class = args.get("guiclass", "")
            if "ArgumentsPanel" in gui_class:
                collection = args.find("collectionProp[@name='Arguments.arguments']")
                if collection is not None:
                    for element_prop in collection.findall("elementProp"):
                        name = get_string_prop(element_prop, "Argument.name")
                        value = get_string_prop(element_prop, "Argument.value")
                        if name:
                            variables[name] = value

        return variables

    def _extract_thread_settings(self) -> ScenarioSettings:
        """Extract ThreadGroup settings.

        Returns:
            ScenarioSettings with thread configuration
        """
        settings = ScenarioSettings()

        if self._root is None:
            return settings

        thread_groups = list(self._root.iter("ThreadGroup"))
        if not thread_groups:
            return settings

        if len(thread_groups) > 1:
            self._warnings.append(
                f"Multiple ThreadGroups found ({len(thread_groups)}), using first only"
            )

        tg = thread_groups[0]

        # Extract thread count and ramp-up
        settings.threads = get_int_prop(tg, "ThreadGroup.num_threads", 1)
        settings.rampup = get_int_prop(tg, "ThreadGroup.ramp_time", 0)

        # Extract duration if scheduler is enabled
        scheduler_enabled = get_bool_prop(tg, "ThreadGroup.scheduler", False)
        if scheduler_enabled:
            settings.duration = get_int_prop(tg, "ThreadGroup.duration")

        # Extract loop count from main controller
        controller = tg.find(".//elementProp[@name='ThreadGroup.main_controller']")
        if controller is not None:
            loops = get_string_prop(controller, "LoopController.loops", "1")
            if loops == "-1":
                settings.loops = 0  # Infinite
            else:
                try:
                    settings.loops = int(loops)
                except ValueError:
                    settings.loops = 1

        return settings

    def _extract_global_headers(self) -> dict[str, str]:
        """Extract global HeaderManager headers (at TestPlan level).

        Returns:
            Dictionary of header name to value
        """
        headers: dict[str, str] = {}

        if self._root is None:
            return headers

        # Find TestPlan
        test_plan = self._root.find(".//TestPlan")
        if test_plan is None:
            return headers

        # Get TestPlan's children
        children = self._get_children(test_plan)
        for child in children:
            if child.tag == "HeaderManager":
                headers.update(self._extract_headers_from_manager(child))

        return headers

    def _extract_samplers(self) -> list[ExtractedSampler]:
        """Extract all HTTP samplers with controller context.

        Uses recursive traversal to track parent controller context
        (RandomController, TransactionController, TestAction).

        Returns:
            List of ExtractedSampler objects
        """
        samplers: list[ExtractedSampler] = []

        if self._root is None:
            return samplers

        # Start from ThreadGroup(s)
        for thread_group in self._root.iter("ThreadGroup"):
            initial_context = ParsingContext()
            self._extract_samplers_recursive(thread_group, initial_context, samplers)

        return samplers

    def _extract_samplers_recursive(
        self,
        element: Element,
        context: ParsingContext,
        results: list[ExtractedSampler],
    ) -> None:
        """Recursively extract samplers tracking parent controller context.

        Args:
            element: Current element being processed
            context: Context from parent chain (random flag, tx name, pending think time)
            results: List to append extracted samplers to
        """
        children = self._get_children(element)
        current_context = context

        for child in children:
            if not is_enabled(child):
                continue

            if child.tag == "RandomController":
                new_ctx = ParsingContext(
                    in_random_controller=True,
                    transaction_name=current_context.transaction_name,
                    pending_think_time=current_context.pending_think_time,
                )
                self._extract_samplers_recursive(child, new_ctx, results)

            elif child.tag == "TransactionController":
                tx_name = get_attribute(child, "testname", "Transaction")
                new_ctx = ParsingContext(
                    in_random_controller=current_context.in_random_controller,
                    transaction_name=tx_name,
                    pending_think_time=current_context.pending_think_time,
                )
                self._extract_samplers_recursive(child, new_ctx, results)

            elif child.tag == "TestAction":
                # TestAction with PAUSE action -> apply to next sampler
                action_type = get_int_prop(child, "TestAction.action", 0)
                if action_type == 1:  # PAUSE action
                    duration = get_int_prop(child, "TestAction.duration", 0)
                    if duration > 0:
                        current_context = ParsingContext(
                            in_random_controller=current_context.in_random_controller,
                            transaction_name=current_context.transaction_name,
                            pending_think_time=duration,
                        )
                # TestAction may have children - recurse
                self._extract_samplers_recursive(child, current_context, results)

            elif child.tag in self.SUPPORTED_SAMPLERS:
                # Extract sampler with accumulated context
                sampler_children = self._get_children(child)
                sampler = self._extract_sampler_data(child, sampler_children)

                # Apply context modifications
                if current_context.in_random_controller:
                    sampler.random = True

                if current_context.transaction_name:
                    sampler.name = f"{current_context.transaction_name}: {sampler.name}"

                if current_context.pending_think_time and sampler.think_time is None:
                    sampler.think_time = current_context.pending_think_time

                results.append(sampler)

                # Clear pending think_time after use
                current_context = ParsingContext(
                    in_random_controller=current_context.in_random_controller,
                    transaction_name=current_context.transaction_name,
                    pending_think_time=None,
                )

            elif child.tag in self.UNSUPPORTED_ELEMENTS:
                reason = self.UNSUPPORTED_ELEMENTS[child.tag]
                name = child.get("testname", child.tag)
                self._warnings.append(f"{name} ignored ({reason})")

            else:
                # Other elements (controllers, etc.) - recurse into them
                self._extract_samplers_recursive(child, current_context, results)

    def _extract_sampler_data(
        self, sampler: Element, children: list[Element]
    ) -> ExtractedSampler:
        """Extract data from a single HTTPSamplerProxy.

        Args:
            sampler: HTTPSamplerProxy element
            children: Child elements (from hashTree)

        Returns:
            ExtractedSampler with extracted data
        """
        name = get_attribute(sampler, "testname", "HTTP Request")
        enabled = is_enabled(sampler)

        method = get_string_prop(sampler, "HTTPSampler.method", "GET")
        path = get_string_prop(sampler, "HTTPSampler.path", "/")
        path = normalize_variable_refs(path)

        # Domain/port/protocol (may override defaults)
        domain = get_string_prop(sampler, "HTTPSampler.domain")
        port = get_string_prop(sampler, "HTTPSampler.port")
        protocol = get_string_prop(sampler, "HTTPSampler.protocol")

        # Extract body or params
        payload, params = self._extract_request_body(sampler)

        # Extract headers (merge global + sampler-specific)
        headers = dict(self._global_headers)
        headers.update(self._extract_headers(children))

        # Extract file uploads
        files = self._extract_files(sampler)

        # Extract captures
        captures = self._extract_captures(children)

        # Extract assertions
        assertions = self._extract_assertions(children)

        # Extract think time
        think_time = self._extract_timers(children)

        # Extract loop config (if sampler is inside a controller)
        loop = self._extract_loop_config(sampler)

        return ExtractedSampler(
            name=name,
            method=method,
            path=path,
            enabled=enabled,
            domain=domain,
            port=port,
            protocol=protocol,
            payload=payload,
            params=params,
            headers=headers,
            files=files,
            captures=captures,
            assertions=assertions,
            loop=loop,
            think_time=think_time,
        )

    def _extract_request_body(
        self, sampler: Element
    ) -> tuple[dict | str | None, dict[str, str]]:
        """Extract request body or parameters from HTTPSamplerProxy.

        Args:
            sampler: HTTPSamplerProxy element

        Returns:
            Tuple of (payload, params) - one will be populated, other empty/None
        """
        is_raw_body = get_bool_prop(sampler, "HTTPSampler.postBodyRaw", False)

        arguments = sampler.find(".//elementProp[@name='HTTPsampler.Arguments']")
        if arguments is None:
            return None, {}

        collection = arguments.find("collectionProp[@name='Arguments.arguments']")
        if collection is None:
            return None, {}

        if is_raw_body:
            # Raw body mode - single argument with body content
            for arg in collection.findall("elementProp"):
                value = get_string_prop(arg, "Argument.value")
                if value:
                    value = strip_carriage_returns(value.strip())
                    if not value:
                        continue
                    # Try to parse as JSON
                    try:
                        return json.loads(value), {}
                    except json.JSONDecodeError:
                        return value, {}  # Keep as raw string
            return None, {}
        else:
            # Form parameters mode
            params: dict[str, str] = {}
            for arg in collection.findall("elementProp"):
                name = get_string_prop(arg, "Argument.name")
                value = get_string_prop(arg, "Argument.value")
                if name:
                    params[name] = normalize_variable_refs(value)
            return None, params

    def _extract_headers(self, children: list[Element]) -> dict[str, str]:
        """Extract headers from HeaderManager children.

        Args:
            children: Child elements of sampler

        Returns:
            Dictionary of header name to value
        """
        headers: dict[str, str] = {}

        for child in children:
            if child.tag == "HeaderManager":
                headers.update(self._extract_headers_from_manager(child))

        return headers

    def _extract_headers_from_manager(self, manager: Element) -> dict[str, str]:
        """Extract headers from a HeaderManager element.

        Args:
            manager: HeaderManager element

        Returns:
            Dictionary of header name to value
        """
        headers: dict[str, str] = {}

        collection = manager.find("collectionProp[@name='HeaderManager.headers']")
        if collection is None:
            return headers

        for element_prop in collection.findall("elementProp"):
            name = get_string_prop(element_prop, "Header.name")
            value = get_string_prop(element_prop, "Header.value")
            if name:
                # Remove leading dash if present (JMeter quirk)
                name = name.lstrip("- ")
                headers[name] = normalize_variable_refs(value)

        return headers

    def _extract_files(self, sampler: Element) -> list[FileConfig]:
        """Extract file upload configuration from HTTPSamplerProxy.

        Args:
            sampler: HTTPSamplerProxy element

        Returns:
            List of FileConfig objects
        """
        files: list[FileConfig] = []

        # Find HTTPsampler.Files elementProp
        file_args = sampler.find(".//elementProp[@name='HTTPsampler.Files']")
        if file_args is None:
            return files

        # Find HTTPFileArgs.files collectionProp
        collection = file_args.find("collectionProp[@name='HTTPFileArgs.files']")
        if collection is None:
            return files

        # Extract each HTTPFileArg
        for file_prop in collection.findall("elementProp"):
            if file_prop.get("elementType") != "HTTPFileArg":
                continue

            path = get_string_prop(file_prop, "File.path")
            param = get_string_prop(file_prop, "File.paramname")
            mime_type = get_string_prop(file_prop, "File.mimetype")

            if path and param:
                # Normalize variable references in path
                path = normalize_variable_refs(path)
                files.append(
                    FileConfig(
                        path=path,
                        param=param,
                        mime_type=mime_type if mime_type else None,
                    )
                )

        return files

    def _extract_captures(self, children: list[Element]) -> list[CaptureConfig]:
        """Extract JSONPostProcessor as captures.

        Args:
            children: Child elements of sampler

        Returns:
            List of CaptureConfig objects
        """
        captures: list[CaptureConfig] = []

        for child in children:
            if child.tag == "JSONPostProcessor" and is_enabled(child):
                ref_names = get_string_prop(child, "JSONPostProcessor.referenceNames")
                json_paths = get_string_prop(child, "JSONPostProcessor.jsonPathExprs")
                match_numbers = get_string_prop(child, "JSONPostProcessor.match_numbers")

                # Handle multiple captures (comma-separated)
                names = [n.strip() for n in ref_names.split(",") if n.strip()]
                paths = [p.strip() for p in json_paths.split(",") if p.strip()]

                # Convert match number
                match, match_warnings = convert_match_number(match_numbers)
                self._warnings.extend(match_warnings)

                for i, name in enumerate(names):
                    path = paths[i] if i < len(paths) else f"$.{name}"
                    captures.append(
                        CaptureConfig(
                            variable_name=name,
                            jsonpath=path,
                            match=match,
                        )
                    )

        return captures

    def _extract_assertions(self, children: list[Element]) -> AssertConfig | None:
        """Extract assertions from children.

        Args:
            children: Child elements of sampler

        Returns:
            AssertConfig or None
        """
        config = AssertConfig()
        has_assertion = False

        for child in children:
            if not is_enabled(child):
                continue

            if child.tag == "ResponseAssertion":
                test_field = get_string_prop(child, "Assertion.test_field")
                test_type = get_int_prop(child, "Assertion.test_type", 8)

                # Note: JMeter has a typo - "Asserion" instead of "Assertion"
                test_strings = child.find("collectionProp[@name='Asserion.test_strings']")
                if test_strings is None:
                    test_strings = child.find("collectionProp[@name='Assertion.test_strings']")

                if test_field == "Assertion.response_code" and test_strings is not None:
                    # Status code assertion
                    for string_prop in test_strings.findall("stringProp"):
                        if string_prop.text:
                            try:
                                config.status = int(string_prop.text)
                                has_assertion = True
                            except ValueError:
                                pass
                            break

                elif test_field == "Assertion.response_data" and test_strings is not None:
                    # Body contains/substring assertion
                    for string_prop in test_strings.findall("stringProp"):
                        if string_prop.text:
                            config.body_contains.append(string_prop.text)
                            has_assertion = True

            elif child.tag == "JSONPathAssertion":
                json_path = get_string_prop(child, "JSON_PATH")
                expected = get_string_prop(child, "EXPECTED_VALUE")

                if json_path and expected:
                    # Convert JSONPath to field name (simplified)
                    field_name = json_path.lstrip("$.")
                    if "." not in field_name and "[" not in field_name:
                        config.body[field_name] = expected
                        has_assertion = True

        return config if has_assertion else None

    def _extract_timers(self, children: list[Element]) -> int | None:
        """Extract timer as think_time.

        Args:
            children: Child elements of sampler

        Returns:
            Think time in milliseconds or None
        """
        for child in children:
            if not is_enabled(child):
                continue

            if child.tag == "ConstantTimer":
                delay = get_int_prop(child, "ConstantTimer.delay", 0)
                if delay > 0:
                    return delay

            elif child.tag == "UniformRandomTimer":
                # Average delay = constant + (range / 2)
                constant = get_int_prop(child, "ConstantTimer.delay", 0)
                range_val = get_int_prop(child, "RandomTimer.range", 0)
                avg_delay = constant + (range_val // 2)
                if avg_delay > 0:
                    return avg_delay

        return None

    def _extract_loop_config(self, element: Element) -> LoopConfig | None:
        """Extract loop configuration if element is inside a controller.

        Args:
            element: Element to check for parent controller

        Returns:
            LoopConfig or None
        """
        # This would require tracking parent elements during tree building
        # For now, we'll handle this in a simplified way
        # TODO: Implement full parent tracking for nested controllers
        return None

    def _build_base_url(self, domain: str, port: str, protocol: str) -> str:
        """Build base URL from components.

        Args:
            domain: Server hostname
            port: Port number
            protocol: http or https

        Returns:
            Base URL string
        """
        if not domain:
            return ""

        protocol = protocol or "http"

        # Default ports can be omitted
        if port and port not in ("80", "443"):
            return f"{protocol}://{domain}:{port}"
        elif port == "443" and protocol == "https":
            return f"https://{domain}"
        elif port == "80" and protocol == "http":
            return f"http://{domain}"
        else:
            return f"{protocol}://{domain}"
