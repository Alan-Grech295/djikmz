from pydantic import BaseModel
from enum import Enum
from typing import Any, Dict, Optional, Set


class WpmlModel(BaseModel):
    """Base class for models that serialize to DJI wpml:-prefixed XML dicts."""

    def to_wpml_dict(self, exclude: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Serialize fields to a dict with wpml: prefix, handling enums and nested models."""
        exclude = exclude or set()
        data = {}
        for name, field in type(self).model_fields.items():
            if name in exclude:
                continue
            value = getattr(self, name)
            if value is None:
                continue
            alias = field.serialization_alias or name
            if isinstance(value, Enum):
                data[alias] = value.value
            elif hasattr(value, 'to_dict'):
                data[alias] = value.to_dict()
            else:
                data[alias] = value
        return {f"wpml:{k}": v for k, v in data.items()}

    @classmethod
    def _alias_map(cls) -> Dict[str, str]:
        """Map serialization aliases (or field names) back to field names."""
        return {
            (f.serialization_alias or name): name
            for name, f in cls.model_fields.items()
        }

    @classmethod
    def _from_wpml_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Strip wpml: prefix and map aliases to field names."""
        alias_map = cls._alias_map()
        return {
            alias_map.get(key.replace("wpml:", ""), key.replace("wpml:", "")): value
            for key, value in data.items()
        }
