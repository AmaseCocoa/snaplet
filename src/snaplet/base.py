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
    _snaplet_metadata: dict[str, tuple] = {}

    def __init__(self, data: dict):
        self._data = data
        self._cache = {}

    def get(self, name: str) -> Any | None:
        if name in self._cache:
            return self._cache[name]

        meta = self._snaplet_metadata.get(name)
        if not meta:
            return self._data.get(name)

        json_key, field_type, base_type, kind, sub_tp = meta
        raw = self._data.get(json_key)
        if raw is None:
            return None

        if kind == "snaplet":
            val = field_type(raw)
        elif kind == "list_snaplet":
            val = [sub_tp(i) for i in raw] if isinstance(raw, list) else raw
        else:
            if isinstance(raw, base_type):
                val = raw
            else:
                try:
                    val = field_type(raw)
                except (TypeError, ValueError):
                    val = raw
        self._cache[name] = val
        return val

    def set(self, name: str, value: Any) -> None:
        meta = self._snaplet_metadata.get(name)
        json_key = meta[0] if meta else name
        self._data[json_key] = getattr(value, "_data", value)
        self._cache[name] = value

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
