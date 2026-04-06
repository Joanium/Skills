---
name: Debug — FastAPI / Django
trigger: fastapi error, django bug, 422 unprocessable entity, pydantic validation error, django orm, django migrations, django 500, fastapi dependency, django settings, celery, django templates, rest framework, drf error
description: Hyper-specific debugging guide for FastAPI and Django. Real errors, real fixes. Covers Pydantic validation, dependency injection, async FastAPI, Django ORM, migrations, DRF, Celery, and settings hell.
---

# Debug — FastAPI / Django

---

# FASTAPI

## First Move

```bash
# Run with auto-reload and full logging
uvicorn app.main:app --reload --log-level debug

# Check interactive docs — test endpoints directly
open http://localhost:8000/docs   # Swagger UI
open http://localhost:8000/redoc  # ReDoc

# See all registered routes
python -c "from app.main import app; [print(r.path, r.methods) for r in app.routes]"

# Run with debugger
uvicorn app.main:app --reload &
python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app
```

---

## 422 Unprocessable Entity — Pydantic Validation Error

This is the most common FastAPI error. Always read the full response body.

```python
# Response body tells you EXACTLY what failed:
# {
#   "detail": [
#     {
#       "loc": ["body", "email"],     ← where the error is
#       "msg": "value is not a valid email address",
#       "type": "value_error.email"   ← what type of error
#     }
#   ]
# }

# Common cause 1: wrong field type in request body
class UserCreate(BaseModel):
    age: int           # client sends "age": "25" (string) → validation error
    age: int | str     # Fix if you need to accept both
    age: int = ...     # age is required, no default
    age: int = 0       # age is optional with default

# Common cause 2: missing required field
class UserCreate(BaseModel):
    name: str          # required — client must send this
    name: str = ""     # optional with default

# Common cause 3: extra fields not allowed
class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')  # Pydantic v2
    # Or in Pydantic v1:
    class Config:
        extra = 'forbid'
    name: str
# Sending extra fields → 422

# Debug: print the exact validation error
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("VALIDATION ERROR:", exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})
```

---

## Dependency Injection Issues

```python
# Error: Can't resolve dependency — usually a missing import or wrong type hint

# Debug: print all dependencies for a route
from fastapi import routing
for route in app.routes:
    if hasattr(route, 'dependencies'):
        print(route.path, route.dependencies)

# Common issue 1: DB session not properly closed
async def get_db():
    db = SessionLocal()
    try:
        yield db          # session available during request
    finally:
        db.close()        # always close — even on error

# Common issue 2: Depends() used in wrong place
@app.get('/users')
async def get_users(db = SessionLocal()):  # WRONG — creates ONE session at startup
async def get_users(db: Session = Depends(get_db)):  # CORRECT — per-request

# Common issue 3: async dependency with sync function
def get_config():         # sync dependency
    return Config()

async def get_settings(): # async dependency
    return await load_settings()

# Mix carefully — FastAPI handles both, but don't await a sync dep
```

---

## Async FastAPI Bugs

```python
# Bug: using sync/blocking code in async endpoint — blocks the event loop
@app.get('/data')
async def get_data():
    time.sleep(5)              # BLOCKS entire server — all requests stall
    result = sync_db_call()    # BLOCKS if not using async ORM

# Fix 1: use async equivalents
@app.get('/data')
async def get_data():
    await asyncio.sleep(5)     # non-blocking
    result = await async_db.fetch_all(query)  # with asyncpg/databases

# Fix 2: run sync in a thread pool
import asyncio
from fastapi.concurrency import run_in_threadpool

@app.get('/data')
async def get_data():
    result = await run_in_threadpool(blocking_sync_function, arg1, arg2)
    return result

# Bug: SQLAlchemy sync ORM in async FastAPI
# If using sync SQLAlchemy, use run_in_threadpool for ALL db calls
# Or switch to SQLAlchemy async (AsyncSession) + asyncpg
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
engine = create_async_engine("postgresql+asyncpg://...")
```

---

## FastAPI Background Tasks

```python
# Bug: background task fails silently
@app.post('/send-email')
async def send_email(background_tasks: BackgroundTasks, data: EmailData):
    background_tasks.add_task(send_email_task, data)
    return {'status': 'queued'}

async def send_email_task(data: EmailData):
    await email_client.send(...)  # if this raises, exception is silently swallowed

# Fix: wrap in try/except and log
async def send_email_task(data: EmailData):
    try:
        await email_client.send(...)
    except Exception as e:
        logger.error(f"Background email task failed: {e}", exc_info=True)
        # Consider: notify via Sentry, push to a dead-letter queue
```

---

# DJANGO

## First Move

```bash
# Check the error in detail
python manage.py runserver  # read the terminal output and browser error page

# Django shell — test queries interactively
python manage.py shell
python manage.py shell_plus  # with django-extensions (better)

# Check settings
python manage.py diffsettings  # shows what differs from default

# Validate the entire project
python manage.py check --deploy  # checks for security and config issues

# Database diagnostics
python manage.py dbshell  # raw SQL shell
python manage.py inspectdb  # introspect existing DB tables
```

---

## Django ORM Debugging

### N+1 Query Problem (Silent Performance Killer)

```python
# N+1: 1 query to get posts, then N queries to get each author
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # triggers a NEW query per post!

# Debug: log all queries
import logging
logging.basicConfig()
logging.getLogger('django.db.backends').setLevel(logging.DEBUG)
# Prints every SQL query to console

# Or use Django Debug Toolbar (development only)
# Shows query count and duplicates in browser

# Fix: select_related for ForeignKey/OneToOne (JOIN)
posts = Post.objects.select_related('author').all()
for post in posts:
    print(post.author.name)  # no extra queries — already joined

# Fix: prefetch_related for ManyToMany/reverse FK (2 queries total)
posts = Post.objects.prefetch_related('tags', 'comments').all()
for post in posts:
    print([t.name for t in post.tags.all()])  # no extra queries

# Check how many queries a view makes
from django.db import connection
print(len(connection.queries))
print(connection.queries)  # list of all executed SQL
```

### QuerySet Not Evaluating (Lazy)

```python
# QuerySets are lazy — no DB hit until evaluated
posts = Post.objects.filter(active=True)  # no DB query yet
# DB query happens when you: iterate, call len(), slice, call .first()/.last(), etc.

# Debug: force evaluation to see what the query produces
list(posts)          # evaluates
print(posts.query)   # prints the raw SQL

# Bug: filtering after evaluation loses queryset laziness
posts = list(Post.objects.all())  # now a Python list
posts.filter(active=True)  # AttributeError — list has no filter()
# Fix: keep as QuerySet until you need the data
posts = Post.objects.filter(active=True)  # QuerySet — chain filters
```

---

## Django Migrations

```bash
# Migrations not applying
python manage.py showmigrations          # see applied/unapplied
python manage.py showmigrations --plan   # execution order

# Detect changes not yet migrated
python manage.py makemigrations --check  # exits non-zero if unmigrated changes

# Squash migration conflicts (two people created migrations)
python manage.py makemigrations --merge  # creates a merge migration

# Nuclear option: fake-apply a migration (when DB state is correct but Django thinks it's not)
python manage.py migrate app_name 0003 --fake

# Recreate from scratch (development only — destroys data!)
python manage.py migrate app_name zero  # unapply all
python manage.py migrate app_name       # re-apply all

# Check the SQL that will run
python manage.py sqlmigrate app_name 0004
```

```python
# Common migration errors:

# "table already exists" — migration ran manually or partially
# Fix: fake the migration
python manage.py migrate --fake-initial

# "column X does not exist" — migration not applied
python manage.py migrate

# CircularDependencyError — two apps depend on each other's migrations
# Fix: use swappable_dependency or restructure your models

# "Cannot add NOT NULL column without a default"
# Fix: add a default in the migration
migrations.AddField(
    model_name='user',
    name='phone',
    field=models.CharField(max_length=20, default=''),  # temporary default
    preserve_default=False,  # removes default from model after migration
)
```

---

## Django Settings Issues

```python
# Wrong settings file loading
# Check which settings are active:
python manage.py shell -c "import django; print(django.conf.settings.SETTINGS_MODULE)"
echo $DJANGO_SETTINGS_MODULE  # check env var

# settings.py checklist for common bugs:
# 1. ALLOWED_HOSTS — must include your domain in production
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
# DisallowedHost error → domain not in ALLOWED_HOSTS

# 2. DEBUG = True in production → 500 errors show tracebacks to users + security risk
# 3. SECRET_KEY in code → should be from environment
SECRET_KEY = os.environ.get('SECRET_KEY')

# 4. STATIC_ROOT not set → collectstatic fails
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 5. DATABASES — SQLite works in dev but watch for write concurrency issues
# For production, always use PostgreSQL

# 6. INSTALLED_APPS missing your app → models not found, migrations not created
INSTALLED_APPS = [
    ...
    'myapp',  # must be here
]
```

---

## Django REST Framework (DRF)

```python
# 403 Forbidden — authentication/permission issue
# Debug:
from rest_framework.request import Request
# Add to view temporarily:
print('user:', request.user)
print('auth:', request.auth)
print('authenticators:', request.authenticators)

# Common: JWT token not being parsed
# Check: Authorization header format — must be "Bearer <token>" not just the token
# Check: DEFAULT_AUTHENTICATION_CLASSES includes your auth class
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

# Serializer validation errors — read the full error
serializer = UserSerializer(data=request.data)
if not serializer.is_valid():
    print(serializer.errors)  # {field: [error_message]}
    return Response(serializer.errors, status=400)

# N+1 in DRF — serializers cause N+1 by default
class PostSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()
    
    def get_author_name(self, post):
        return post.author.name  # N+1 query per post!

# Fix: override get_queryset() with select_related
class PostViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Post.objects.select_related('author').all()
```

---

## Celery (Django background tasks)

```bash
# Start worker with verbose logging
celery -A myproject worker -l DEBUG

# Start beat scheduler (periodic tasks)
celery -A myproject beat -l DEBUG

# Inspect running workers
celery -A myproject inspect active
celery -A myproject inspect registered  # all registered tasks

# Purge all pending tasks
celery -A myproject purge

# Debug a specific task
python manage.py shell
from myapp.tasks import my_task
result = my_task.delay(arg1, arg2)
print(result.get(timeout=30))  # blocks waiting for result
print(result.state)            # PENDING / STARTED / SUCCESS / FAILURE
print(result.traceback)        # if FAILURE — the full traceback
```

```python
# Common Celery bugs:

# Task not found — worker doesn't see your task
# Fix: restart the worker after adding new tasks (workers load tasks at startup)
# Also check CELERY_IMPORTS or autodiscover:
app.autodiscover_tasks()  # discovers tasks.py in all INSTALLED_APPS

# Tasks running but silently failing
# Fix: always use try/except and track failures
@app.task(bind=True, max_retries=3)
def send_notification(self, user_id):
    try:
        user = User.objects.get(id=user_id)
        notify(user)
    except User.DoesNotExist as e:
        logger.error(f"User {user_id} not found")
        raise  # don't retry — programming error
    except NotificationError as e:
        logger.warning(f"Notification failed, retrying: {e}")
        raise self.retry(exc=e, countdown=60)  # retry after 60s
```
