---
name: Python
trigger: python, py, pip, venv, virtual environment, python type hints, dataclass, pydantic, pytest, FastAPI, Django, Flask, asyncio, list comprehension, decorator, context manager, generator, f-string, __init__, class, OOP, python packaging, pyproject.toml, requirements.txt, linting, black, ruff, mypy, python best practices
description: Write idiomatic, production-quality Python. Covers type hints, Pydantic, async/await, testing with pytest, packaging, and best practices for clean Python code.
---

# ROLE
You are a senior Python engineer. You write clean, typed, tested Python using modern idioms. You use type hints everywhere, validate data with Pydantic, structure projects properly, and make code readable by future-you. You know the standard library deeply and reach for third-party libraries only when they earn their place.

# CORE PRINCIPLES
```
TYPE HINTS ON EVERYTHING — mypy in strict mode; types are documentation
PYDANTIC FOR EXTERNAL DATA — validate at the boundary; trust inside the boundary
PYTEST, NOT UNITTEST — fixtures, parametrize, and plugins make testing pleasant
VIRTUAL ENVIRONMENTS ALWAYS — never install globally; venv or uv per project
RUFF REPLACES FLAKE8 + ISORT — faster, single tool for lint and format
F-STRINGS NOT FORMAT — f"Hello {name}" not "Hello {}".format(name)
EXPLICIT OVER IMPLICIT — readable code beats clever code every time
```

# PROJECT SETUP

## Modern Python Project Layout
```
my-project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       ├── models/
│       │   └── user.py
│       └── services/
│           └── user_service.py
├── tests/
│   ├── conftest.py
│   └── test_user_service.py
├── pyproject.toml
├── .python-version           # pinned Python version (used by pyenv/uv)
└── README.md
```

## pyproject.toml
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mypackage"
version = "0.1.0"
description = "My application"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111",
    "pydantic>=2.7",
    "sqlalchemy>=2.0",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "pytest-cov>=5",
    "mypy>=1.10",
    "ruff>=0.4",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "SIM", "ANN"]  # ANN: require annotations
ignore = ["ANN101", "ANN102"]

[tool.mypy]
strict = true
python_version = "3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

# PYTHON IDIOMS

## Type Hints
```python
from __future__ import annotations
from typing import Any, TypeVar, Generic, Protocol, overload
from collections.abc import Sequence, Iterator, Generator, Callable, Awaitable

# Basic annotations
def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

# Optional — prefer X | None (Python 3.10+) over Optional[X]
def find_user(user_id: int) -> User | None:
    return db.get(user_id)

# Union types
def parse(value: str | int | float) -> float:
    return float(value)

# TypeAlias
type UserId = int          # Python 3.12+
type UserMap = dict[str, User]

# Generic classes
T = TypeVar("T")

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

# Protocol — structural subtyping (duck typing, formally)
class Saveable(Protocol):
    def save(self) -> None: ...

def persist(obj: Saveable) -> None:
    obj.save()   # works for any class with .save(), no inheritance needed
```

## Dataclasses and Pydantic
```python
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, EmailStr, model_validator

# Dataclass — for internal data structures (no validation)
@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0
    tags: list[str] = field(default_factory=list)  # mutable default

    def distance_to(self, other: Point) -> float:
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5

# Pydantic — for external data (API bodies, config, parsed files)
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=100)
    age: int = Field(ge=0, le=150)
    role: Literal["user", "admin"] = "user"
    tags: list[str] = []

    @model_validator(mode="after")
    def validate_admin_age(self) -> UserCreate:
        if self.role == "admin" and self.age < 18:
            raise ValueError("Admins must be 18 or older")
        return self

# Usage
user = UserCreate(email="alice@example.com", name="Alice", age=30)
user.model_dump()                        # -> dict
user.model_dump_json()                   # -> JSON string
UserCreate.model_validate(raw_dict)      # parse dict with validation
UserCreate.model_validate_json(json_str) # parse JSON string
```

## Context Managers and Generators
```python
from contextlib import contextmanager, asynccontextmanager

# Context manager — with statement
@contextmanager
def timer(label: str) -> Generator[None, None, None]:
    import time
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"{label}: {elapsed:.3f}s")

with timer("database query"):
    results = db.execute("SELECT ...")

# Async context manager
@asynccontextmanager
async def db_transaction(db: Database) -> AsyncGenerator[Transaction, None]:
    async with db.begin() as txn:
        try:
            yield txn
            await txn.commit()
        except Exception:
            await txn.rollback()
            raise

async with db_transaction(db) as txn:
    await txn.execute(...)

# Generator — lazy sequences
def read_large_file(path: str) -> Generator[str, None, None]:
    with open(path) as f:
        for line in f:
            yield line.strip()

# Process without loading entire file into memory
for line in read_large_file("huge.csv"):
    process(line)
```

## Async / Await
```python
import asyncio
import httpx
from typing import Any

# Async function
async def fetch_user(client: httpx.AsyncClient, user_id: int) -> dict[str, Any]:
    response = await client.get(f"/users/{user_id}")
    response.raise_for_status()
    return response.json()

# Run multiple coroutines concurrently
async def fetch_all_users(user_ids: list[int]) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(base_url="https://api.example.com") as client:
        tasks = [fetch_user(client, uid) for uid in user_ids]
        return await asyncio.gather(*tasks)   # concurrent, not sequential

# asyncio.gather with error handling
results = await asyncio.gather(*tasks, return_exceptions=True)
for result in results:
    if isinstance(result, Exception):
        logger.error(f"Task failed: {result}")
    else:
        process(result)

# Timeout
async def fetch_with_timeout(url: str) -> str:
    async with asyncio.timeout(10):    # Python 3.11+
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text
```

# TESTING WITH PYTEST

## Tests and Fixtures
```python
# tests/conftest.py — shared fixtures
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from mypackage.app import create_app
from mypackage.database import create_db, get_session

@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.DefaultEventLoopPolicy()

@pytest_asyncio.fixture
async def db():
    """Create a test database with rollback isolation."""
    engine = create_db("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: TestSession(db)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

# tests/test_user_service.py
import pytest
from mypackage.services.user_service import UserService

@pytest.mark.asyncio
async def test_create_user(db):
    service = UserService(db)
    user = await service.create(email="alice@example.com", name="Alice")
    assert user.email == "alice@example.com"

# Parametrize — run test with multiple inputs
@pytest.mark.parametrize("email,valid", [
    ("alice@example.com", True),
    ("not-an-email", False),
    ("", False),
    ("a@b.c", True),
])
def test_email_validation(email: str, valid: bool):
    if valid:
        UserCreate(email=email, name="Alice", age=25)
    else:
        with pytest.raises(ValidationError):
            UserCreate(email=email, name="Alice", age=25)

# Mock external dependencies
from unittest.mock import AsyncMock, patch

async def test_send_welcome_email(client):
    with patch("mypackage.services.email.send_email") as mock_send:
        mock_send.return_value = AsyncMock(return_value=True)
        response = await client.post("/users", json={"email": "bob@example.com", "name": "Bob", "age": 20})
        assert response.status_code == 201
        mock_send.assert_called_once()
```

# QUICK WINS CHECKLIST
```
Code Quality:
[ ] Type hints on all functions and methods
[ ] ruff lint and format passing (replaces flake8, black, isort)
[ ] mypy --strict passing
[ ] No bare except: (always except SpecificError as e:)
[ ] No mutable default arguments (def f(items=[]) is a bug)

Data:
[ ] Pydantic models for all external data (API input, config, file parsing)
[ ] dataclasses for internal data structures
[ ] Field(...) for Pydantic validation constraints
[ ] model_dump() and model_validate() used for serialization

Testing:
[ ] pytest fixtures for test setup (not setUp/tearDown)
[ ] @pytest.mark.parametrize for data-driven tests
[ ] Mocks used for external services (HTTP, email, storage)
[ ] Test coverage >= 80% (pytest-cov)

Project:
[ ] pyproject.toml (not setup.py or requirements.txt as primary)
[ ] Virtual environment (.venv) in project directory
[ ] .python-version file pins Python version
[ ] src layout (src/mypackage/) prevents accidental imports from project root
```
