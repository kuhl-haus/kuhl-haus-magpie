# AGENTS.md — kuhl-haus-magpie

> Instructions for AI agents assisting with code maintenance of this repository.

## What Is Magpie?

Magpie is a **site monitoring and synthetic transaction service** built on Django + Celery. It runs three types of canary checks against configured endpoints:

1. **HTTP Health Check** — GET request, validate status code or JSON response body
2. **TLS Certificate Check** — connect via SSL, calculate days until cert expiration
3. **DNS Check** — query configured resolvers, validate DNS responses

Results are posted to **Graphite** via the Carbon pickle protocol. Endpoints and check configurations are managed through Django Admin (themed with Unfold). Celery Beat schedules the canary tasks.

Magpie consolidates code from two archived predecessor packages (`kuhl-haus-canary` and `kuhl-haus-metrics`) into a single codebase.

## Repository Layout

```
src/kuhl_haus/magpie/
├── __init__.py              # Package version + Celery app import workaround
├── api.py                   # FastAPI/Uvicorn entrypoint (dev server)
├── manage.py                # Django management command entrypoint
├── canary/                  # Core canary task implementations (pure functions)
│   ├── env.py               # Canary environment variables
│   └── tasks/
│       ├── dns_check.py     # DNS query logic
│       ├── http_health_check.py  # HTTP health check logic
│       └── tls.py           # TLS certificate expiration check
├── canary_tasks/
│   └── tasks.py             # Celery task wrappers (Django ORM → canary functions → Carbon)
├── metrics/                 # Metrics collection and posting
│   ├── env.py               # Metrics environment variables
│   ├── data/
│   │   └── metrics.py       # Metrics dataclass (counters, attributes, Carbon format, JSON)
│   ├── clients/
│   │   └── carbon_poster.py # Graphite Carbon pickle protocol client
│   ├── factories/
│   │   └── logs.py          # Structured JSON logger factory
│   └── models/
│       └── carbon_config.py # CarbonConfig dataclass
├── endpoints/               # Django app for endpoint management
│   ├── models.py            # EndpointModel, ScriptConfig, DnsResolver, DnsResolverList
│   ├── admin.py             # Django Admin (Unfold theme, Celery Beat integration)
│   ├── api_views.py         # DRF ViewSets
│   ├── serializers.py       # DRF serializers
│   └── urls.py              # API router
├── database/                # Django app for DB bootstrap
│   └── management/commands/bootstrap.py  # migrate + collectstatic + create superuser
├── web/                     # Django project configuration
│   ├── settings.py          # All Django settings (env-var driven)
│   ├── urls.py              # URL routing (admin, API, Swagger, health checks)
│   ├── celery_app.py        # Celery app configuration
│   ├── health.py            # /health and /healthz endpoints
│   ├── context_processors.py # Template context (version, domain info)
│   ├── wsgi.py / asgi.py    # WSGI/ASGI entry points
│   └── templates/           # Base template + index page
tests/
├── canary/tasks/            # Tests for DNS, HTTP, TLS canary functions
├── metrics/                 # Tests for Metrics, CarbonPoster, CarbonConfig, logger
├── conftest.py              # (empty — available for shared fixtures)
└── test_settings.py         # Minimal Django settings for test runs
```

## Architecture

```
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Celery Beat  │────>│ Celery Worker│────>│  Canary Task │
   │ (scheduler)  │     │              │     │  Functions   │
   └──────────────┘     └──────────────┘     └──────┬───────┘
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                              │                     │                     │
                        ┌─────▼───────┐       ┌─────▼──────┐      ┌───────▼─────┐
                        │ HTTP Health │       │  TLS Check │      │  DNS Check  │
                        │   Check     │       │            │      │             │
                        └─────┬───────┘       └─────┬──────┘      └───────┬─────┘
                              │                     │                     │
                              └─────────────────────┼─────────────────────┘
                                                    │
                                             ┌──────▼──────┐     ┌──────────┐
                                             │ CarbonPoster│────>│ Graphite │
                                             │  (pickle)   │     │  Server  │
                                             └─────────────┘     └──────────┘

   ┌──────────────┐     ┌──────────────┐
   │ Django Admin │────>│  PostgreSQL  │  (SQLite for development)
   │  (Unfold)    │     │   Database   │
   └──────────────┘     └──────────────┘

   ┌──────────────┐
   │  Django Web  │──── /health, /healthz, /admin/, /api/
   │  (Gunicorn)  │
   └──────────────┘
```

**Key separation:** Canary task *implementations* (`canary/tasks/`) are pure functions that accept models, metrics, and a logger — no Django ORM dependency. The Celery task *wrappers* (`canary_tasks/tasks.py`) handle ORM queries, CarbonPoster instantiation, and batch posting. This separation is what enables the high test coverage on the core logic.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python ≥ 3.12 |
| Web framework | Django 5.2.x |
| Task queue | Celery 5.6.x + django-celery-beat + django-celery-results |
| API | Django REST Framework + drf-yasg (Swagger/ReDoc) |
| Admin theme | django-unfold |
| Metrics transport | Graphite Carbon pickle protocol (custom `CarbonPoster`) |
| DNS | dnspython |
| TLS | pyOpenSSL + ssl (stdlib) |
| HTTP checks | requests |
| Database | PostgreSQL (production) / SQLite (dev/test) |
| ASGI server | Uvicorn + Gunicorn |
| Package manager | PDM |
| Build backend | pdm-backend |
| CI/CD | GitHub Actions |
| Container registry | ghcr.io |
| PyPI | Trusted Publisher (Sigstore-signed releases) |

## Development Environment

### Prerequisites

- Python ≥ 3.12
- PDM (`pip install pdm`)

### Setup

```bash
git clone https://github.com/kuhl-haus/kuhl-haus-magpie.git
cd kuhl-haus-magpie
pip install -r requirements.txt
pdm install
```

### Running Tests

```bash
# Standard test run
pdm run pytest tests -v

# With coverage (mirrors CI)
pdm run pytest --cov=kuhl_haus.magpie --cov-report=html --cov-report=xml tests -v
```

**Important:** The `pytest.ini` sets `DJANGO_SETTINGS_MODULE=kuhl_haus.magpie.web.settings`. Tests use SQLite by default (no `POSTGRES_HOST` env var). Do not set `POSTGRES_HOST` unless you have a test database available.

### Running Locally

```bash
# Django dev server
python -m kuhl_haus.magpie.manage runserver 0.0.0.0:8000

# Or via the FastAPI/Uvicorn entrypoint
python -m kuhl_haus.magpie.api
```

## Branching & Release

- **Default branch:** `mainline`
- **Legacy branch:** `v0.2.x` (no longer active)
- **Releases:** Git tags trigger the full CI/CD pipeline: build → test → Docker images → GitHub Release → TestPyPI → PyPI
- **Tag format:** `v{major}.{minor}.{patch}` (e.g., `v0.5.2`)
- **Current version:** defined in `pyproject.toml` → `version = "0.5.2"`

### CI/CD Pipeline (GitHub Actions)

The single workflow `publish-to-pypi.yml` runs on every push:

1. **Build and Test** — installs deps, runs pytest with coverage, uploads coverage to Codecov (tags only), builds sdist + wheel
2. **Build Docker** — builds and pushes 4 container images to `ghcr.io/kuhl-haus/`:
   - `kuhl-haus-magpie` (Django web — `Dockerfile`)
   - `kuhl-haus-magpie-beat` (Celery Beat — `Dockerfile.celery_beat`)
   - `kuhl-haus-magpie-worker` (Celery Worker — `Dockerfile.celery_worker`)
   - `kuhl-haus-magpie-flower` (Flower dashboard — `Dockerfile.flower`)
3. **GitHub Release** (tags only) — creates release with Sigstore-signed artifacts
4. **Publish to TestPyPI** (tags only)
5. **Publish to PyPI** (tags only)

### Docker Images

All Dockerfiles use `python:3.13` as base, install from `requirements.txt`, and run `docker-entrypoint.sh` (which runs the `bootstrap` management command: migrate + collectstatic + create superuser).

Image tags: `{version}` + `latest` for tagged builds; `{version}-{short_hash}` for non-tagged builds.

## File Encoding Warning

⚠️ **`requirements.txt` is UTF-16 LE encoded** (with BOM). Standard Unix tools like `grep`, `sed`, and `awk` will not work on it. Use Python with `encoding='utf-16'` for any programmatic modifications:

```python
with open('requirements.txt', 'r', encoding='utf-16') as f:
    content = f.read()

# Make changes to content...

with open('requirements.txt', 'w', encoding='utf-16', newline='\r\n') as f:
    f.write(content)
```

Git diffs will show `Binary files ... differ` for this file — that is expected.

## Test Coverage

- **Overall:** ~55% (due to Django admin/views/ORM code lacking tests)
- **Core canary and metrics code:** 97%+ coverage
- **Well-tested modules:**
  - `canary/tasks/dns_check.py` — DNS query logic, error handling, resolver fallback
  - `canary/tasks/http_health_check.py` — HTTP checks, JSON response handling, timeouts
  - `canary/tasks/tls.py` — TLS cert expiration calculation, error handling
  - `metrics/data/metrics.py` — Metrics dataclass, Carbon format, version conversion
  - `metrics/clients/carbon_poster.py` — Carbon pickle protocol, input validation
  - `metrics/models/carbon_config.py` — Config loading and validation
  - `metrics/factories/logs.py` — Logger factory
- **Not tested (Django layer):**
  - `canary_tasks/tasks.py` — Celery task wrappers (ORM queries + batch posting)
  - `endpoints/` — models, admin, API views, serializers
  - `web/` — settings, URLs, templates, context processors
  - `database/` — bootstrap management command

**Rule:** Do not decrease coverage. New code in the core canary/metrics modules must include tests. Django layer tests are welcome but not required.

## Dependency Management

- **`pyproject.toml`** declares direct runtime dependencies (unpinned) and optional `[testing]` extras
- **`pdm.lock`** is the resolved lockfile managed by PDM
- **`requirements.txt`** is a fully-pinned freeze file used by Docker builds and CI — this is what Dependabot scans
- When updating dependencies, update `requirements.txt` (respecting its UTF-16 LE encoding) and regenerate `pdm.lock` if needed

### Dependabot

Dependabot is configured for daily pip updates and weekly Docker updates. As of the latest check, there are multiple open alerts — primarily Django CVEs and a cryptography vulnerability. Dependabot may not be able to auto-fix transitive dependency conflicts (as seen with cryptography requiring coordinated pyOpenSSL and cffi bumps).

## Environment Variables

Magpie is configured entirely through environment variables. Key ones:

| Variable | Purpose | Default |
|----------|---------|---------|
| `DJANGO_SETTINGS_MODULE` | Django settings module | `kuhl_haus.magpie.web.settings` |
| `DJANGO_SECRET_KEY` | Django secret key | insecure dev default |
| `DJANGO_DEBUG` | Debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | derived from `MAGPIE_DOMAIN` |
| `POSTGRES_HOST` | PostgreSQL host (if unset → SQLite) | None |
| `POSTGRES_DB/USER/PASSWORD/PORT` | PostgreSQL connection | `magpie` / `magpie` / `magpie` / `5432` |
| `CELERY_BROKER_URL` | Celery broker (e.g., Redis/RabbitMQ URL) | None |
| `MAGPIE_DOMAIN` | Domain for cookies/CSRF/CORS | `localhost` |
| `FLOWER_DOMAIN` | Flower dashboard domain | `localhost:5555` |
| `DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD` | Bootstrap superuser | `admin` / `admin@example.com` / None |
| `CARBON_SERVER_IP` | Graphite server IP | None |
| `CARBON_PICKLE_PORT` | Carbon pickle port | `2004` |
| `IMAGE_VERSION` / `CONTAINER_IMAGE` | Container metadata for health endpoint | `Unknown` |

## Key Design Patterns

### Canary Function Signature

All canary task implementations follow the same pattern:

```python
def invoke_check(ep: EndpointModel, metrics: Metrics, logger: Logger):
    # 1. Set request counter
    # 2. Perform the check
    # 3. Record response time
    # 4. Set response/error/exception counters
    # 5. Populate metrics.attributes with results
```

They never raise exceptions to the caller — all errors are captured in `metrics.attributes['exception']` and counted via `metrics.set_counter('exceptions', 1)`.

### Celery Task Wrapper Pattern

Each Celery task in `canary_tasks/tasks.py` follows the same structure:

1. Load `ScriptConfig` from DB by name
2. Query `EndpointModel` objects filtered by check type
3. Instantiate `CarbonPoster`
4. Loop through endpoints → create `Metrics` → invoke canary function → collect carbon tuples
5. Batch-post metrics to Carbon (batch size 64)
6. Return status dict

**DRY opportunity:** The three task functions (`http_health_check`, `tls_check`, `dns_check`) share ~80% identical boilerplate. Refactoring into a common task runner is a known improvement area.

### Metrics → Carbon Format

The `Metrics` dataclass generates Graphite-compatible metric paths:

```
{namespace}.{name}.mnemonic.{mnemonic}.{key};{tag1}={val1};{tag2}={val2}
{namespace}.{name}.mnemonic.{mnemonic}.{key}
{namespace}.{name}.hostname.{dotless_hostname}.{key}
```

Each metric is a tuple: `(path, (timestamp, value))`. Only numeric values (int, float, or numeric strings) are included.

## Common Maintenance Tasks

### Updating Dependencies

1. Modify version pins in `requirements.txt` (remember: UTF-16 LE encoding!)
2. Verify resolution: create a venv and `pip install -r requirements.txt`
3. Run tests: `pytest tests -v`
4. Check for transitive conflicts (e.g., pyOpenSSL capping cryptography)

### Adding a New Canary Check Type

1. Create `src/kuhl_haus/magpie/canary/tasks/new_check.py` with a pure function
2. Write tests in `tests/canary/tasks/test_new_check.py`
3. Add the Celery task wrapper in `canary_tasks/tasks.py`
4. Add relevant fields to `EndpointModel` if needed (+ migration)
5. Update admin in `endpoints/admin.py` if new fields are added

### Adding an Endpoint Model Field

1. Add field to `EndpointModel` in `endpoints/models.py`
2. Run `python -m kuhl_haus.magpie.manage makemigrations`
3. Update `endpoints/serializers.py` to include the new field
4. Update `endpoints/admin.py` fieldsets and list_display
5. Update relevant canary functions if the field affects check behavior

### Bumping the Version for Release

1. Update `version` in `pyproject.toml`
2. Commit with message format: `Version X.Y.Z - description`
3. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
4. GHA pipeline handles the rest (build → test → Docker → PyPI)

## Coding Standards

- **Python ≥ 3.12** — use modern syntax (type hints, f-strings, `match` statements where appropriate)
- **Line length:** 88 characters (flake8 config in `pyproject.toml`)
- **Docstrings:** Follow existing patterns — the `Metrics` class has comprehensive docstrings as a reference
- **Test naming:** `test_{function_name}_{scenario}` (e.g., `test_query_dns_successful_first_resolver`)
- **Test fixtures:** Use pytest fixtures, `unittest.mock.patch` for external dependencies
- **Test data:** Use RFC 5737 TEST-NET addresses (`192.0.2.x`) for IP addresses in tests
- **Commit messages:** Conventional-ish format — `[version X.Y.Z] description` or `Fix/feat: description`

## Known Issues and Debt

1. **`.coveragerc` references wrong package name** — `source = bedrock_magpie` should be `kuhl_haus.magpie` (the CI command overrides this with `--cov=kuhl_haus.magpie`)
2. **`api.py` mixes FastAPI and Django WSGI** — the `app = web_wsgi.application` line assigns a WSGI app to what should be a FastAPI app. The production Dockerfiles use Gunicorn, not this entrypoint.
3. **Celery task boilerplate duplication** — the three task functions in `canary_tasks/tasks.py` are nearly identical; a common task runner pattern would reduce ~200 lines
4. **CHANGELOG.rst is minimal** — only covers v0.1
5. **`requirements.txt` UTF-16 LE encoding** — unusual; breaks standard tooling. Consider converting to UTF-8
6. **40+ open Dependabot alerts** — primarily Django CVEs needing coordinated version bumps
7. **No pre-commit hooks configured** — `.pre-commit-config.yaml` referenced in docs but doesn't exist
8. **`CORS_ALLOWED_ORIGINS` defaults to `"*"`** — the settings code passes this string directly; `django-cors-headers` expects a list for `CORS_ALLOWED_ORIGINS` (though `"*"` works with `CORS_ALLOW_ALL_ORIGINS`)

## Security Considerations

- Never commit secrets or credentials — all sensitive values come from environment variables
- The `SECURITY.md` file contains the project's vulnerability reporting process and PGP key
- Container images are signed with Sigstore
- CodeQL scanning runs on every push
- Dependabot monitors both pip and Docker dependencies

## Owner

This repository is maintained by Tom Pounders ([@oldschool-engineer](https://github.com/oldschool-engineer)). AI contributions require review and approval before merge.
