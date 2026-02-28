import sys
import textwrap
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Type,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

_CAMEL_CACHE: Dict[str, str] = {}


def to_camel_case(snake_str: str) -> str:
    if snake_str in _CAMEL_CACHE:
        return _CAMEL_CACHE[snake_str]
    components = snake_str.split("_")
    res = components[0] + "".join(x.title() for x in components[1:])
    _CAMEL_CACHE[snake_str] = sys.intern(res)
    return _CAMEL_CACHE[snake_str]


def _get_json_key(field_name: str, field_type: Any) -> str:
    if get_origin(field_type) is Annotated:
        for meta in get_args(field_type)[1:]:
            if hasattr(meta, "alias") and meta.alias:
                return cast(str, meta.alias)
    return to_camel_case(field_name)


def _get_base_type(tp: Any) -> Any:
    origin = get_origin(tp)
    if origin is Union:
        return get_args(tp)
    if origin is not None:
        return origin
    return tp


class SnapletMeta(type):
    def __new__(mcs, name, bases, attrs, jit=True):
        if "__slots__" not in attrs:
            attrs["__slots__"] = ()

        attrs["__snaplet_jit__"] = jit

        cls = super().__new__(mcs, name, bases, attrs)
        setattr(cls, "_snaplet_fields", {})
        if name == "SnapletBase":
            return cls

        hints = get_type_hints(cls, include_extras=True)
        fields_map = {}
        for field_name, field_type in hints.items():
            if field_name.startswith("_") or field_name in attrs:
                continue

            json_key = _get_json_key(field_name, field_type)
            base_type = _get_base_type(field_type)
            fields_map[field_name] = json_key

            if jit:
                prop = mcs._compile_accessor(
                    field_name, json_key, field_type, base_type
                )
            else:
                prop = mcs._create_dynamic_accessor(
                    field_name, json_key, field_type, base_type
                )

            setattr(cls, field_name, prop)
        setattr(cls, "_snaplet_fields", fields_map)

        return cls

    def __init__(cls, name, bases, attrs, jit=True):
        super().__init__(name, bases, attrs)

    @staticmethod
    def _create_dynamic_accessor(
        name: str, json_key: str, field_type: Type, base_type: Type
    ):
        def get_kind(tp):
            origin = get_origin(tp)
            if origin in (list, List):
                args = get_args(tp)
                if args:
                    sub_tp = args[0]
                    if hasattr(sub_tp, "_snaplet_fields"):
                        return "list_snaplet", sub_tp
            if hasattr(tp, "_snaplet_fields"):
                return "snaplet", tp
            return "scalar", None

        kind, sub_tp = get_kind(field_type)

        def fget(self):
            if name in self._cache:
                return self._cache[name]
            raw = self._data.get(json_key)
            if raw is None:
                return None

            if kind == "snaplet":
                val = field_type(raw)
            elif kind == "list_snaplet":
                st = cast(Type[Any], sub_tp) 
                val = [st(i) for i in raw] if isinstance(raw, list) else raw
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

        def fset(self, value):
            self._data[json_key] = getattr(value, "_data", value)
            self._cache[name] = value

        return property(fget, fset)

    @staticmethod
    def _compile_accessor(
        name: str, json_key: str, field_type: Type, base_type: Type
    ):
        def is_snaplet_type(tp):
            origin = get_origin(tp)
            if origin is list or origin is List:
                args = get_args(tp)
                if args and hasattr(args[0], "_snaplet_fields"):
                    return "list_snaplet", args[0]
            if hasattr(tp, "_snaplet_fields"):
                return "snaplet", tp
            return "scalar", None

        kind, sub_tp = is_snaplet_type(field_type)

        if kind == "snaplet":
            cast_logic = "val = __T(raw)"
        elif kind == "list_snaplet":
            cast_logic = "val = [__SUB_T(i) for i in raw] if isinstance(raw, list) else raw"
        else:
            cast_logic = textwrap.dedent("""
                if isinstance(raw, __B):
                    val = raw
                else:
                    try:
                        val = __T(raw)
                    except (TypeError, ValueError):
                        val = raw""").strip()

        template = textwrap.dedent(f"""\
            def _getter(self):
                if '{name}' in self._cache:
                    return self._cache['{name}']
                raw = self._data.get('{json_key}')
                if raw is None:
                    return None
                {textwrap.indent(cast_logic, "                ").lstrip()}
                self._cache['{name}'] = val
                return val

            def _setter(self, value):
                self._data['{json_key}'] = getattr(value, '_data', value)
                self._cache['{name}'] = value
        """)

        namespace = {"__T": field_type, "__B": base_type, "__SUB_T": sub_tp if sub_tp is not None else object}
        exec(template.strip(), namespace)

        return property(fget=namespace["_getter"], fset=namespace["_setter"])
