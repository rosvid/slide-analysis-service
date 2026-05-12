import inspect
from abc import ABC, abstractmethod
from typing import Any, Optional

from pptx.presentation import Presentation
from pypdfium2 import PdfDocument

from core.dtos import RuleResultDto
from core.enums import RuleId


class BaseRule(ABC):
    """
    Abstract base class for all presentation analysis rules.
    """
    RULE_ID: RuleId = None

    @property
    def rule_id(self) -> RuleId:
        if self.RULE_ID is None:
            raise NotImplementedError(f"{self.__class__.__name__} must define the RULE_ID class variable.")
        return self.RULE_ID

    @abstractmethod
    def apply(self, pptx: Presentation | None, pdf: PdfDocument | None) -> RuleResultDto:
        pass

    def get_parameters(self) -> dict[str, dict[str, Any]]:
        """
        Retrieves the parameters of the class's `__init__` method along with their types and default values.

        This method is needed for the use of API for the threshold parameters (e.g. min font size) for the analysis rules.
        """
        parameters: dict[str, dict[str, Any]] = {}
        try:
            signature = inspect.signature(self.__init__)
        except (ValueError, TypeError):
            return parameters

        for name, parameter in signature.parameters.items():
            if name == "self":
                continue
            default = None if parameter.default is inspect.Signature.empty else parameter.default
            # value = getattr(self, name, default)
            if parameter.annotation is inspect.Signature.empty:
                parameter_type: Optional[str] = None
            else:
                # Turn annotation into a readable string.
                annotation = parameter.annotation
                parameter_type = getattr(annotation, "__name__", str(annotation))
            parameters[name] = {"type": parameter_type, "default": default}
        return parameters
