---
name: Debug — Python
trigger: python error, python bug, traceback, attributeerror, typeerror, importerror, keyerror, indexerror, valueerror, nameerror, recursionerror, segfault python, python slow, memory error, python not working
description: Hyper-specific debugging guide for Python. Real tracebacks, real causes, real fixes. Covers runtime exceptions, import errors, async bugs, type pitfalls, virtual environment hell, and performance issues.
---

# Debug — Python

## First Move: Read the Full Traceback

Python tracebacks go **bottom-up** — the actual error is at the bottom, the call chain is above it.

```bash
# Run with full traceback (default)
python -m mymodule  # preferred over python mymodule.py

# Verbose import debugging
python -v script.py 2>&1 | grep -i "import\|error"

# Check your Python version
python --version
which python  # are you in the right venv?

# Check installed packages in current environment
pip list | grep package_name
pip show package_name  # version, location, dependencies

# Environment health check
python -c "import sys; print(sys.executable, sys.version, sys.path)"
```

---

## Virtual Environment Hell

Most "it worked yesterday" Python bugs are environment issues.

```bash
# Create a clean venv
python -m venv .venv

# Activate (pick your shell)
source .venv/bin/activate        # bash/zsh
.venv\Scripts\activate           # Windows cmd
source .venv/Scripts/activate    # Windows git bash

# Verify you're in the right env
which python   # should point inside .venv/
pip list       # should be minimal

# Install dependencies
pip install -r requirements.txt
# Or with extras:
pip install -e ".[dev]"   # editable install with dev deps

# Freeze current working state
pip freeze > requirements.txt

# Nuclear option — nuke and rebuild
deactivate
rm -rf .venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## ImportError / ModuleNotFoundError

```bash
# 1. Check if package is installed in the ACTIVE environment
pip show requests  # if nothing prints, it's not installed

# 2. Wrong Python / pip mismatch — check they point to same env
which python && which pip
python -m pip install package  # guarantees the right pip

# 3. Relative import outside of package
# Error: attempted relative import with no known parent package
# Fix: run as module, not as script
python -m mypackage.module  # correct
python mypackage/module.py  # broken for relative imports

# 4. Circular import — A imports B, B imports A
# Symptom: ImportError or partially initialized module
# Debug: add print at top of each module to trace load order
# Fix options:
#   a) Move the import inside the function that needs it
#   b) Restructure to break the cycle
#   c) Use TYPE_CHECKING guard for type-only imports
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .models import User  # only imported at type-check time, not runtime

# 5. __init__.py missing — package not recognized
ls mypackage/__init__.py  # must exist (can be empty)
touch mypackage/__init__.py
```

---

## AttributeError

### `'NoneType' object has no attribute 'X'`

```python
# Something returned None that you expected to return an object
user = get_user(id)  # returns None if not found
user.name            # AttributeError

# Debug: find what returned None
print(f"get_user returned: {repr(user)}")

# Fix: guard before access
if user is None:
    raise ValueError(f"User {id} not found")
user.name  # safe

# Or use assert for quick debugging (remove in prod)
assert user is not None, f"Expected user for id={id}, got None"
```

### `module 'X' has no attribute 'Y'`

```python
# 1. Outdated API — check the installed version's docs
import package; print(package.__version__)
# Then check changelog for when Y was added/removed

# 2. Shadowing stdlib with your own file
# Error: you named your file 'json.py' or 'os.py' etc.
ls json.py  # rename this file

# 3. Lazy/conditional export — attribute only exists under certain conditions
# Check the source: where is Y defined? Is it behind an if block?
import inspect
print(inspect.getfile(package))  # find where package lives
```

---

## KeyError / IndexError

```python
# KeyError — key doesn't exist in dict
config['database_url']  # KeyError if missing

# Fix 1: .get() with default
url = config.get('database_url', 'sqlite:///default.db')

# Fix 2: .setdefault() — insert if missing, return value
url = config.setdefault('database_url', 'sqlite:///default.db')

# Fix 3: raise informative error
if 'database_url' not in config:
    raise KeyError(f"'database_url' missing from config. Keys present: {list(config.keys())}")

# IndexError — list access out of bounds
items[5]  # IndexError if len(items) <= 5

# Debug: always check length
print(f"len(items)={len(items)}, trying index 5")

# Fix: guard
if len(items) > 5:
    item = items[5]
else:
    item = None  # or default, or raise

# Safe access pattern
item = next(iter(items[5:6]), None)  # returns None if not enough elements
```

---

## TypeError

### Wrong argument count / types

```python
# Python 3.10+ gives great messages:
# TypeError: process() takes 2 positional arguments but 3 were given

# Debug: check the signature
import inspect
print(inspect.signature(process))

# Common cause: forgetting 'self' in method call
class Handler:
    def process(self, data): ...

handler = Handler()
Handler.process(data)      # TypeError — missing self
handler.process(data)      # correct

# Passing wrong types
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")  # returns "12" — no error but wrong! Use mypy to catch this
# Run: mypy script.py
```

### `'X' object is not iterable`

```python
# Trying to iterate something that isn't iterable
for item in None:  # TypeError
for item in 42:    # TypeError

# Debug: check what the value actually is
val = get_items()
print(f"type={type(val)}, val={repr(val)}")

# Wrap in safety
items = get_items() or []  # if falsy (None, False, 0), use empty list
for item in (items if items is not None else []):
    ...
```

---

## ValueError

```python
# int('abc')      → invalid literal for int() with base 10: 'abc'
# float('inf')    → valid! but may cause downstream issues
# list.remove(x)  → x not in list

# Safe int conversion
def to_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

# Check before remove
if item in my_list:
    my_list.remove(item)
# Or use discard for sets:
my_set.discard(item)  # no error if not present
```

---

## Mutable Default Argument (Silent Killer)

```python
# THE most common Python gotcha — default is shared across all calls
def append_to(item, lst=[]):  # lst is created ONCE at function definition
    lst.append(item)
    return lst

append_to(1)  # [1]
append_to(2)  # [1, 2] ← NOT [2]!  lst persists between calls

# Fix: always use None as default, create inside function
def append_to(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

---

## Async / asyncio Bugs

```python
# 1. Calling async function without await — gets a coroutine, not the result
async def fetch():
    return await httpx.get('/api')

result = fetch()        # result is <coroutine object> — never ran!
result = await fetch()  # correct

# Detect: Python warns "coroutine 'fetch' was never awaited"

# 2. Mixing sync and async — blocking the event loop
import time
async def bad():
    time.sleep(5)  # BLOCKS the entire event loop — no other tasks run

async def good():
    await asyncio.sleep(5)  # yields control — other tasks can run

# 3. Running sync DB calls inside async code
# Use asyncio.to_thread() to run blocking code in a thread pool
async def get_user(user_id):
    user = await asyncio.to_thread(db.query, User, user_id)
    return user

# 4. asyncio.run() called inside already running loop (e.g., Jupyter)
# Error: "This event loop is already running"
# Fix for Jupyter:
import nest_asyncio
nest_asyncio.apply()

# 5. Gathering tasks — exception in one kills all
results = await asyncio.gather(task1(), task2(), task3())
# Fix: use return_exceptions=True
results = await asyncio.gather(task1(), task2(), task3(), return_exceptions=True)
for r in results:
    if isinstance(r, Exception):
        print("Task failed:", r)
```

---

## Recursion / Stack Overflow

```python
# RecursionError: maximum recursion depth exceeded
# Default limit is 1000

# Debug: print depth
def recurse(n, depth=0):
    print(f"depth={depth}, n={n}")
    return recurse(n - 1, depth + 1)

# Temporary increase (find the real bug — don't leave this in)
import sys
sys.setrecursionlimit(5000)

# Fix: convert to iterative with explicit stack
def walk_tree(root):
    stack = [root]
    while stack:
        node = stack.pop()
        if node is None:
            continue
        print(node.value)
        stack.extend([node.left, node.right])

# Fix: use functools.lru_cache for recursive memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

---

## Performance Debugging

```python
# Profile where time is actually spent
import cProfile
cProfile.run('my_function()', sort='cumulative')

# Line-by-line profiling
pip install line_profiler
@profile  # decorator added by line_profiler
def my_function():
    ...
kernprof -l -v script.py

# Memory profiling
pip install memory_profiler
@profile
def my_function():
    ...
python -m memory_profiler script.py

# Quick timing
import timeit
timeit.timeit('"-".join(str(n) for n in range(100))', number=10000)

# Find slow DB queries (SQLAlchemy)
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Debugging Tools

```python
# pdb — built-in debugger
import pdb; pdb.set_trace()  # breakpoint, old style
breakpoint()                  # Python 3.7+ — same thing

# pdb commands:
# n (next line), s (step into), c (continue), l (list code)
# p var (print var), pp var (pretty print), q (quit)
# b 42 (set breakpoint at line 42), w (where in stack)

# ipdb — better pdb with tab completion
pip install ipdb
import ipdb; ipdb.set_trace()

# Rich — beautiful debug printing
pip install rich
from rich import print, inspect
inspect(obj, methods=True)  # full object inspection

# icecream — automatic variable printing
pip install icecream
from icecream import ic
ic(variable)  # prints: ic| variable: <value>
ic(function())  # prints function name + return value
```

---

## mypy Type Checking

```bash
# Install and run
pip install mypy
mypy script.py
mypy --strict script.py  # stricter checks

# Common mypy errors and fixes:

# error: Function is missing a return type annotation
def process(data):         # bad
def process(data: dict) -> str:  # good

# error: Incompatible return value type (got "None", expected "str")
def get_name() -> str:
    if user:
        return user.name
    # Fix: add return or change return type to Optional[str]
    return ""

# error: Item "None" of "Optional[X]" has no attribute "Y"
def show(user: Optional[User]):
    user.name  # error — could be None
    if user: user.name  # fix

# Ignore a specific line (use sparingly)
x = bad_function()  # type: ignore[return-value]

# Config file: mypy.ini
[mypy]
python_version = 3.11
strict = True
ignore_missing_imports = True
```
