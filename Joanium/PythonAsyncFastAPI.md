---
name: Python Async FastAPI
trigger: fastapi, async python, asyncio, pydantic, python api, python async, uvicorn, starlette, async def, await, httpx async, async sqlalchemy, python rest api, fastapi router, fastapi dependency injection
description: Build high-performance Python APIs with FastAPI and asyncio — covering async patterns, Pydantic models, dependency injection, async SQLAlchemy, background tasks, middleware, and deployment.
---

# ROLE
You are a senior Python engineer specializing in async FastAPI services. You write correct async code, use Pydantic for all I/O, and structure FastAPI apps for testability and horizontal scale.

# CORE ASYNC CONCEPTS
```python
# async def — suspends with await, doesn't block the event loop
async def fetch_user(user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

# await — pauses this coroutine, lets event loop run other tasks
# Only valid inside async def

# BLOCKING vs NON-BLOCKING
# ✗ Blocks the event loop — starves all other requests
def bad_handler():
    time.sleep(5)          # sync sleep blocks
    data = requests.get()  # sync HTTP blocks

# ✓ Non-blocking — event loop runs other coroutines while waiting
async def good_handler():
    await asyncio.sleep(5)    # async sleep
    async with httpx.AsyncClient() as client:
        data = await client.get(url)

# For CPU-bound work — run in thread pool to avoid blocking
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

async def cpu_intensive():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, sync_heavy_function, arg)
```

# FASTAPI PROJECT STRUCTURE
```
app/
├── main.py                 ← app factory, lifespan, middleware
├── api/
│   ├── deps.py             ← shared dependencies (db session, current user)
│   └── v1/
│       ├── router.py       ← aggregates all v1 routes
│       ├── users.py        ← user endpoints
│       └── orders.py
├── models/                 ← SQLAlchemy ORM models
│   └── user.py
├── schemas/                ← Pydantic request/response schemas
│   └── user.py
├── crud/                   ← DB operations (async functions)
│   └── user.py
├── core/
│   ├── config.py           ← Settings from env vars
│   ├── security.py         ← JWT, hashing
│   └── database.py         ← async engine + session factory
└── tests/
```

# MAIN APP + LIFESPAN
```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.database import engine
from app.models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="My API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")
```

# PYDANTIC SCHEMAS
```python
# schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=100)
    email: EmailStr | None = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}  # enables .model_validate(orm_obj)

# Nested schemas
class OrderResponse(BaseModel):
    id: str
    total: float
    user: UserResponse     # embedded
    items: list[ItemResponse]

    model_config = {"from_attributes": True}
```

# ASYNC DATABASE WITH SQLALCHEMY 2.0
```python
# core/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,    # postgresql+asyncpg://user:pass@host/db
    pool_size=20,
    max_overflow=0,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)

# crud/user.py
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.schemas.user import UserCreate

async def get_user(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 20) -> list[User]:
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())

async def create_user(db: AsyncSession, data: UserCreate) -> User:
    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)   # reload after commit to get DB-generated fields
    return user

async def delete_user(db: AsyncSession, user_id: str) -> bool:
    result = await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return result.rowcount > 0
```

# DEPENDENCY INJECTION
```python
# api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.core.security import verify_token

# DB session — auto-closes after request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Current user from JWT
security = HTTPBearer()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await crud.get_user(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Admin guard
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

# ROUTER + ENDPOINTS
```python
# api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app import crud
from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.require_admin)   # admin only
):
    return await crud.get_users(db, skip=skip, limit=limit)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(deps.get_current_user)):
    return current_user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: AsyncSession = Depends(deps.get_db),
    _: User = Depends(deps.get_current_user)
):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(deps.get_db)
):
    existing = await crud.get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    return await crud.create_user(db, data)
```

# BACKGROUND TASKS
```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str, name: str):
    # Runs after response is sent — don't block request
    await email_service.send(to=email, template="welcome", context={"name": name})

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(deps.get_db)
):
    user = await crud.create_user(db, data)
    background_tasks.add_task(send_welcome_email, user.email, user.name)
    return user   # response sent immediately, email sent after
```

# PARALLEL ASYNC CALLS
```python
# Sequential — slow (one after another)
user = await get_user(user_id)
orders = await get_orders(user_id)
posts = await get_posts(user_id)

# Parallel — fast (all at once with asyncio.gather)
user, orders, posts = await asyncio.gather(
    get_user(user_id),
    get_orders(user_id),
    get_posts(user_id)
)

# With error handling — return_exceptions catches per-task errors
results = await asyncio.gather(
    task_a(), task_b(), task_c(),
    return_exceptions=True
)
for result in results:
    if isinstance(result, Exception):
        logger.error(f"Task failed: {result}")
```

# SETTINGS FROM ENVIRONMENT
```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "case_sensitive": True}

settings = Settings()
```

# COMMON MISTAKES TO AVOID
```
✗ Mixing sync and async — sync DB calls (psycopg2) inside async def block the event loop
✗ Not awaiting coroutines — forgetting await returns a coroutine object, not a value
✗ Using requests instead of httpx in async code — requests is sync
✗ Not using async with for session — session leaks if exception occurs before close
✗ Creating a new engine per request — create once at startup
✗ Not using return_exceptions in gather — one failure cancels all tasks
✗ Putting logic in schema validators — keep schemas dumb, logic in service layer
✗ Missing model_config from_attributes=True — .model_validate(orm_obj) will fail
```
