import pytest

from snaplet import SnapletBase


class User(SnapletBase, jit=True):
    user_id: int
    user_name: str
    is_active: bool


class FastUser(SnapletBase):
    user_id: int
    name: str

    def __init__(self, *args, **kwargs):
        self.init_called = True
        super().__init__(*args, **kwargs)


class Child(SnapletBase, jit=True):
    name: str


class Parent(SnapletBase, jit=True):
    child: Child


class NestedModel(SnapletBase):
    id: int
    tags: list[str]


def test_basic_functionality():
    data = {"userId": 1, "userName": "gemini", "isActive": True}
    user = User(data)

    assert user.user_id == 1
    assert user.user_name == "gemini"
    assert user.is_active is True
    assert user._data is data


@pytest.mark.parametrize(
    "input_val, expected",
    [
        ("123", 123),
        (10.5, 10),
        ("invalid", "invalid"),
        (None, None),
    ],
)
def test_type_casting(input_val, expected):
    class CastModel(SnapletBase, jit=True):
        val: int

    m = CastModel({"val": input_val})
    assert m.val == expected


def test_nested_model():
    data = {"child": {"name": "son"}}
    parent = Parent(data)

    assert isinstance(parent.child, Child)
    assert parent.child.name == "son"
    assert parent.child is parent.child
