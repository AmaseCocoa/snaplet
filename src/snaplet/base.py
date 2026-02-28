from typing import (
    Any,
    TypeVar,
)

import orjson

from .meta import SnapletMeta

T = TypeVar("T", bound="SnapletBase")


class SnapletBase(metaclass=SnapletMeta):
    __slots__ = ("_data", "_cache")
    _snaplet_fields: dict[str, str] = {}

    def __init__(self, data: dict):
        self._data = data
        self._cache = {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.to_dict()})"

    @classmethod
    def bulk_load(cls: type[T], data: bytes | list) -> list[T]:
        items = orjson.loads(data) if isinstance(data, bytes) else data

        new_obj = cls.__new__
        results = []

        for item in items:
            obj = new_obj(cls)
            object.__setattr__(obj, "_data", item)
            object.__setattr__(obj, "_cache", {})
            results.append(obj)

        return results

    @classmethod
    def load_json(cls, data: str | bytes) -> "SnapletBase":
        j = orjson.loads(data)
        obj = cls.__new__(cls)
        object.__setattr__(obj, "_data", j)
        object.__setattr__(obj, "_cache", {})
        return obj

    def to_dict(self) -> dict[str, Any]:
        result = self._data.copy()

        for field_name, value in self._cache.items():
            json_key = self._snaplet_fields.get(field_name, field_name)

            if isinstance(value, SnapletBase):
                result[json_key] = value.to_dict()
            elif isinstance(value, list):
                result[json_key] = [
                    item.to_dict() if isinstance(item, SnapletBase) else item
                    for item in value
                ]
            else:
                result[json_key] = value
        return result

    def to_json(self) -> bytes:
        if not self._cache:
            return orjson.dumps(self._data)

        return orjson.dumps(self.to_dict())
