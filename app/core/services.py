import importlib
import inspect
import logging
import os
import pkgutil
from typing import Optional

import core.rules
from core.analysers.pdf_analyser import PdfAnalyser
from core.analysers.ppt_analyser import PptAnalyser
from core.analysers.pptx_analyser import PptxAnalyser
from core.dtos import AnalysisResultDto
from core.rules.base_rule import BaseRule

logger = logging.getLogger(__name__)


class AnalyserService:
    """
    Manages the analysis of uploaded files using various rules and handlers (for different format).
    """

    def __init__(self):
        self.analysers = {
            ".pptx": PptxAnalyser(),
            ".ppt": PptAnalyser(),
            # Example for possible PDF analysis.
            ".pdf": PdfAnalyser(),
        }
        self.all_rules = [rule_class() for rule_class in _REGISTERED_RULES]
        self.rules_map = {rule.rule_id.value: rule for rule in self.all_rules}

    def analyse(self, uploaded_file, rules_config: Optional[list[str]] = None) -> AnalysisResultDto:
        _, file_extension = os.path.splitext(uploaded_file.name)
        file_extension = file_extension.lower()

        analyser = self.analysers.get(file_extension)
        if not analyser:
            raise ValueError(f"Unsupported file type: '{file_extension}'")

        rules_to_apply = self._prepare_rules(rules_config)
        analysis_data = analyser.analyse(uploaded_file, file_extension, rules_to_apply)

        return analysis_data

    def _prepare_rules(self, rules_config: list[str] | None) -> list[BaseRule]:
        """
        Parses the rules' configurations from the request and prepares the corresponding rule instances with parameters.
        """
        # Fallback to all default rules if no specific configuration is provided.
        if not rules_config:
            return self.all_rules

        prepared_rules: list[BaseRule] = []

        # Parse the config string to separate the rule ID from its optional parameter.
        for config_str in rules_config:
            rule_id, sep, param_value = config_str.partition(":")
            if not sep:
                param_value = None

            # Look up the base rule object. Skip silently (with debug log) if it doesn't exist.
            if (rule_template := self.rules_map.get(rule_id)) is None:
                logger.debug(f"Unknown rule id '{rule_id}' requested. Skipping.")
                continue

            # If no parameter provided or the rule itself doesn't accept any parameters; use the default rule template.
            if param_value is None or not (params := rule_template.get_parameters()):
                prepared_rules.append(rule_template)
                continue

            # Extract the expected name and type of the rule's first parameter.
            param_name = next(iter(params))
            param_type_name = params[param_name].get("type", "str")

            try:
                # Cast the string parameter value from the config to the required Python type.
                match param_type_name:
                    case "int":
                        typed_value = int(param_value)
                    case "float":
                        typed_value = float(param_value)
                    case "bool":
                        typed_value = param_value.lower() in ("true", "1", "yes")
                    case _:
                        typed_value = str(param_value)

                # Create an instance of the rule class, passing the typed parameter.
                # noinspection PyArgumentList
                new_rule_instance = type(rule_template)(**{param_name: typed_value})
                prepared_rules.append(new_rule_instance)

            except (ValueError, TypeError) as e:
                # If type casting fails; fall back to the default rule template.
                logger.warning(
                    f"Invalid parameter '{param_value}' for rule '{rule_id}'. "
                    f"Expected type {param_type_name}. Falling back to default. Error: {e}"
                )
                prepared_rules.append(rule_template)

        return prepared_rules


class RulesService:
    """
    Contains services to receive and manage a collection of rules.
    """

    def __init__(self):
        self.rules = [rule_class() for rule_class in _REGISTERED_RULES]

    def get_rules(self):
        return [
            {
                "id": rule.rule_id.value,
                "description": rule.rule_id.description,
                "parameters": rule.get_parameters(),
            }
            for rule in self.rules
        ]

    def get_rule_by_id(self, rule_id: str):
        for rule in self.rules:
            if rule.rule_id.value == rule_id:
                return {
                    "id": rule.rule_id.value,
                    "description": rule.rule_id.description,
                    "parameters": rule.get_parameters(),
                }
        return None


def _load_rules() -> list[type[BaseRule]]:
    """
    Dynamically loads all rule classes from the core.rules package.
    """
    loaded_classes: list[type[BaseRule]] = []
    # Iterate all files in rules package to find all rules.
    for module_info in pkgutil.walk_packages(core.rules.__path__, core.rules.__name__ + "."):
        try:
            module = importlib.import_module(module_info.name)

            # Get all rule classes.
            for _, cls in inspect.getmembers(module, inspect.isclass):
                # Get all subclasses of BaseRule.
                if issubclass(cls, BaseRule) and cls is not BaseRule:
                    # Check, if class is defined in the current module.
                    if cls.__module__ == module.__name__:
                        loaded_classes.append(cls)

        except ImportError as e:
            logger.exception(f"Error importing {module_info.name}: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error loading rules from {module_info.name}: {e}")

    return loaded_classes


# Load rules once when the module is imported, so they are available for all instances of the services without needing to reload them.
_REGISTERED_RULES: list[type[BaseRule]] = _load_rules()
