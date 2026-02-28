# Snaplet
Faster JSON Mapping, the only dependency is orjson.

## Features
* **Just-In-Time (JIT) Codegen**:
Snaplet generates specialized property accessors at runtime using `exec()`. By eliminating `getattr` calls and internal dictionary lookups during access, it achieves near-native attribute access speeds.
* **Zero-Copy Lazy Instantiation**:
Nested models and lists are only instantiated when accessed. This minimizes the performance impact when processing large JSON payloads where only specific fields are required.
* **High-Throughput Bulk Loading**:
Bypasses the standard `__init__` constructor and leverages `__slots__` with `__new__` to mass-produce instances. This enables high-speed loading by reducing Python-level overhead during object creation.
* **Explicit Validation Control**:
Snaplet does not perform eager validation on load. This design allows developers to implement custom validation logic only where necessary, avoiding global performance bottlenecks.
* **Transparent Alias Mapping**:
Supports `Annotated` and `Field(alias=...)` to map complex JSON keys to Pythonic names. JIT compilation ensures that using aliases does not incur additional runtime performance costs.
* **Minimal Dependency**:
The only requirement is `orjson`. It operates as a pure Python library utilizing JIT logic, ensuring high portability across different environments without the need for complex build chains.


## Installation
```bash
uv add snaplet
```

## Usage
```python
from typing import Annotated

from snaplet import SnapletBase
from snaplet import Field


class User(SnapletBase):
    user_id: int
    internal_id: Annotated[int, Field(alias="ID")]
    tags: Annotated[list[str], Field(alias="Tags-List-V1")]


data = {"userId": 1, "ID": 999, "Tags-List-V1": ["python", "snaplet"]}

user = User(data)
print(user.internal_id)
print(user.user_id)
```

You can disable JIT with `jit=False` but, this is not recommended as it may significantly degrade performance.

```python
class User(SnapletBase, jit=False):
    user_id: int
    internal_id: Annotated[int, Field(alias="ID")]
    tags: Annotated[list[str], Field(alias="Tags-List-V1")]
```

## Performance

Snaplet is designed for high-performance applications that handle large JSON datasets with minimal overhead.

### Benchmark (1,000 items)
Measured on Python 3.12.

| Operation | Time | Notes |
| :--- | :--- | :--- |
| **Bulk Load** | **~108 μs** | Using `orjson` + `__new__` bypass |
| **Attribute Access** | **~115 ns** | Powered by JIT Property Access |
| **Lazy Export (dict)** | **~165 ns** | Zero-cost for unaccessed fields |

### Why so fast?
- **JIT Property Access**: Specialized property accessors are compiled at runtime using `exec()`, eliminating branch overhead.
- **Lazy Instantiation**: Nested objects are only instantiated when accessed.
- **Minimal Overhead**: Bypassing `__init__` during bulk loading to achieve near-native speeds.

## LICENSE
MIT License