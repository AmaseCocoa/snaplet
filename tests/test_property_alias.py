from typing import Annotated

from snaplet import SnapletBase


class Field:
    def __init__(self, alias: str):
        self.alias = alias


class MySnaplet(SnapletBase):
    @property
    def my_prop(self) -> Annotated[str, Field(alias="myProp")]:
        return self._cache.get("my_prop", self._data.get("myProp"))

    @my_prop.setter
    def my_prop(self, value: str):
        self._cache["my_prop"] = value


def test_property_alias():
    data = {"myProp": "initial"}
    obj = MySnaplet(data)

    assert obj.my_prop == "initial"

    obj.my_prop = "updated"
    assert obj.my_prop == "updated"

    d = obj.to_dict()
    assert d["myProp"] == "updated", "Property alias should be used in to_dict"
    assert "my_prop" not in d


def test_inherited_property_alias():
    class DerivedSnaplet(MySnaplet):
        pass

    data = {"myProp": "initial"}
    obj = DerivedSnaplet(data)

    assert obj.my_prop == "initial"

    obj.my_prop = "updated"
    d = obj.to_dict()
    assert d["myProp"] == "updated"
