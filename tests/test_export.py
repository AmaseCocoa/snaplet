from typing import List, Optional

import orjson

from snaplet import SnapletBase


class Item(SnapletBase):
    id: int
    name: str


class User(SnapletBase):
    id: int
    name: str
    tags: List[str]
    items: List[Item]
    extra: Optional[str] = None


raw_json = b"""
[
    {
        "id": 1,
        "name": "Alice",
        "tags": ["rust", "python"],
        "items": [{"id": 10, "name": "Bob"}],
        "extra": null
    }
]
"""


def test_output_integrity():
    users = User.bulk_load(raw_json)
    user = users[0]

    user.name = "Bob"
    user.tags.append("jit")

    d = user.to_dict()
    assert d["name"] == "Bob", "書き換えた値が反映されていること"
    assert "jit" in d["tags"], "リスト操作が反映されていること"
    assert d["id"] == 1, "触っていない値が保持されていること"
    assert isinstance(d["items"][0], dict), (
        "ネストしたモデルが dict に戻っていること"
    )
    assert d["items"][0]["name"] == "Bob"


def test_orjson_serialization():
    users = User.bulk_load(raw_json)
    user = users[0]

    json_bytes = user.to_json()
    reparsed = orjson.loads(json_bytes)

    assert reparsed["id"] == 1
    assert reparsed["items"][0]["id"] == 10
