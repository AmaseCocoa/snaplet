from typing import (
    Any, List, Type, TypeVar, Union, overload, 
    Sequence, Iterable, cast, SupportsIndex
)

T = TypeVar("T", bound="SnapletBase")

class SnapList(List[Any]):
    __slots__ = ("_model_cls",)

    def __init__(self, raw_data: list, model_cls: Type[T]):
        super().__init__(raw_data)
        self._model_cls = model_cls

    @overload
    def __getitem__(self, i: SupportsIndex) -> T: ...

    @overload
    def __getitem__(self, s: slice) -> "SnapList[T]": ...

    def __getitem__(self, i: Union[SupportsIndex, slice]) -> Union[T, "SnapList[T]"]:
        # 1. インデックスアクセス (SupportsIndex は int を含む)
        if isinstance(i, (int, SupportsIndex)):
            idx = int(i)
            item = super().__getitem__(idx)
            
            if isinstance(item, dict):
                wrapped = self._model_cls(item)
                self[idx] = wrapped  # インスタンス化したものをキャッシュ
                return wrapped
            return cast(T, item)

        # 2. スライスアクセス
        elif isinstance(i, slice):
            raw_slice = super().__getitem__(i)
            # スライスされたリストを新しい SnapList で包んで返す（Lazyの継続）
            return SnapList(raw_slice, self._model_cls)

        else:
            raise TypeError(f"List indices must be integers or slices, not {type(i).__name__}")

    def __iter__(self) -> Iterable[T]:
        for i in range(len(self)):
            yield self[i]