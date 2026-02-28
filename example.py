from typing import Annotated

from snaplet.base import SnapletBase
from snaplet.field import Field


class User(SnapletBase):
    user_id: int
    internal_id: Annotated[int, Field(alias="ID")]
    tags: Annotated[list[str], Field(alias="Tags-List-V1")]


data = {"userId": 1, "ID": 999, "Tags-List-V1": ["python", "snaplet"]}

user = User(data)
print(user.internal_id)
print(user.user_id)
