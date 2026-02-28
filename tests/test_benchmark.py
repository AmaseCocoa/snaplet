from typing import List

import orjson
import pytest

from snaplet import SnapletBase


class SubItem(SnapletBase):
    id: int
    value: str


class RootModel(SnapletBase):
    id: int
    items: List[SubItem]
    meta: str


large_list_data = [{"id": i, "value": f"val_{i}"} for i in range(1000)]
large_single_data = {"id": 1, "meta": "important", "items": large_list_data}
large_json_bytes = orjson.dumps([large_single_data])


@pytest.mark.benchmark(group="parse")
def test_bench_parse_standard(benchmark):
    def action():
        data = orjson.loads(large_json_bytes)
        return [RootModel(d) for d in data]

    benchmark(action)


@pytest.mark.benchmark(group="parse")
def test_bench_parse_bulk(benchmark):
    benchmark(lambda: RootModel.bulk_load(large_json_bytes))


@pytest.mark.benchmark(group="access")
def test_bench_jit_deep_access(benchmark):
    obj = RootModel.bulk_load(large_json_bytes)[0]
    _ = obj.items[0].value
    benchmark(lambda: obj.items[0].value)


@pytest.mark.benchmark(group="access")
def test_bench_nojit_deep_access(benchmark):
    class NoJITRoot(RootModel, jit=False):
        pass

    obj = NoJITRoot.bulk_load(large_json_bytes)[0]
    _ = obj.items[0].value
    benchmark(lambda: obj.items[0].value)


@pytest.mark.benchmark(group="export")
def test_bench_export_dict(benchmark):
    obj = RootModel.bulk_load(large_json_bytes)[0]
    benchmark(lambda: obj.to_dict())


@pytest.mark.benchmark(group="export")
def test_bench_export_json(benchmark):
    obj = RootModel.bulk_load(large_json_bytes)[0]
    benchmark(lambda: obj.to_json())
