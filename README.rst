|License| |PyPI| |Downloads| |Build Status| |CodeQL| |codecov| |GitHub issues| |GitHub pull requests|

.. |License| image:: https://img.shields.io/github/license/kuhl-haus/kuhl-haus-magpie
   :alt: License
   :target: https://github.com/kuhl-haus/kuhl-haus-magpie/blob/mainline/LICENSE.txt

.. |PyPI| image:: https://img.shields.io/pypi/v/kuhl-haus-magpie.svg
   :alt: PyPI
   :target: https://pypi.org/project/kuhl-haus-magpie/

.. |Downloads| image:: https://static.pepy.tech/badge/kuhl-haus-magpie/month
   :alt: Downloads
   :target: https://pepy.tech/project/kuhl-haus-magpie

.. |Build Status| image:: https://github.com/kuhl-haus/kuhl-haus-magpie/actions/workflows/publish-to-pypi.yml/badge.svg
   :alt: Build Status
   :target: https://github.com/kuhl-haus/kuhl-haus-magpie/actions/workflows/publish-to-pypi.yml

.. |CodeQL| image:: https://github.com/kuhl-haus/kuhl-haus-magpie/workflows/CodeQL/badge.svg
   :alt: CodeQL
   :target: https://github.com/kuhl-haus/kuhl-haus-magpie/actions/workflows/github-code-scanning/codeql/

.. |codecov| image:: https://codecov.io/gh/kuhl-haus/kuhl-haus-magpie/branch/mainline/graph/badge.svg
   :alt: codecov
   :target: https://codecov.io/gh/kuhl-haus/kuhl-haus-magpie

.. |GitHub issues| image:: https://img.shields.io/github/issues/kuhl-haus/kuhl-haus-magpie
   :alt: GitHub issues
   :target: https://github.com/kuhl-haus/kuhl-haus-magpie/issues

.. |GitHub pull requests| image:: https://img.shields.io/github/issues-pr/kuhl-haus/kuhl-haus-magpie
   :alt: GitHub pull requests
   :target: https://github.com/kuhl-haus/kuhl-haus-magpie/pulls


================
kuhl-haus-magpie
================

**Site monitoring and synthetic transaction service** built on Django and Celery.

Magpie runs scheduled canary checks against your HTTP endpoints and reports results to Graphite for dashboarding and alerting. It provides a Django Admin interface for managing endpoints and a REST API for programmatic access.

What It Does
============

Magpie performs three types of canary checks on configured endpoints:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Check
     - What It Does
   * - **HTTP Health Check**
     - Sends a GET request and validates the response status code or JSON body
   * - **TLS Certificate Check**
     - Connects via SSL and calculates days until certificate expiration
   * - **DNS Check**
     - Queries configured DNS resolvers and validates the response

Results — including response times, error counts, and check-specific attributes — are posted to a **Graphite** server via the Carbon pickle protocol.

Architecture
============

.. code-block:: text

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

**Celery Beat** triggers canary tasks on a schedule you define through the Django Admin. **Celery Workers** execute the checks and batch-post metrics to your Graphite server. The **Django web application** provides endpoint management, health check endpoints, and a Swagger/ReDoc API.

Tech Stack
==========

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Component
     - Technology
   * - Language
     - Python ≥ 3.12
   * - Web framework
     - Django 5.2
   * - Task queue
     - Celery + django-celery-beat + django-celery-results
   * - API
     - Django REST Framework + drf-yasg (Swagger/ReDoc)
   * - Admin theme
     - django-unfold
   * - Metrics transport
     - Graphite Carbon pickle protocol
   * - DNS checks
     - dnspython
   * - TLS checks
     - pyOpenSSL
   * - Database
     - PostgreSQL (production) / SQLite (development)
   * - ASGI server
     - Uvicorn + Gunicorn

Quick Start
===========

Install from PyPI
-----------------

.. code-block:: bash

   pip install kuhl-haus-magpie

Run with Docker
---------------

Pre-built container images are published to GitHub Container Registry. A full deployment requires four containers:

.. list-table::
   :header-rows: 1
   :widths: 55 45

   * - Image
     - Purpose
   * - ``ghcr.io/kuhl-haus/kuhl-haus-magpie:latest``
     - Django web application
   * - ``ghcr.io/kuhl-haus/kuhl-haus-magpie-worker:latest``
     - Celery worker (executes canary tasks)
   * - ``ghcr.io/kuhl-haus/kuhl-haus-magpie-beat:latest``
     - Celery Beat (task scheduler)
   * - ``ghcr.io/kuhl-haus/kuhl-haus-magpie-flower:latest``
     - Flower (Celery monitoring dashboard)

Each container runs ``docker-entrypoint.sh`` on startup, which bootstraps the database (migrations, static files, superuser creation).

Development Setup
-----------------

.. code-block:: bash

   git clone https://github.com/kuhl-haus/kuhl-haus-magpie.git
   cd kuhl-haus-magpie
   pip install -r requirements.txt
   pdm install

   # Run the Django development server
   python -m kuhl_haus.magpie.manage runserver 0.0.0.0:8000

   # Run tests
   pdm run pytest tests -v

   # Run tests with coverage
   pdm run pytest --cov=kuhl_haus.magpie --cov-report=html tests -v

Configuration
=============

Magpie is configured entirely through environment variables. No configuration files are required.

Application Settings
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``DJANGO_SECRET_KEY``
     - Django secret key
     - Insecure dev default
   * - ``DJANGO_DEBUG``
     - Enable debug mode
     - ``True``
   * - ``DJANGO_ALLOWED_HOSTS``
     - Comma-separated allowed hosts
     - Derived from ``MAGPIE_DOMAIN``
   * - ``MAGPIE_DOMAIN``
     - Domain for cookies, CSRF, and CORS
     - ``localhost``
   * - ``DISABLE_HTTPS``
     - Disable HTTPS cookie/session settings
     - ``False``

Database
--------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``POSTGRES_HOST``
     - PostgreSQL host (if unset, uses SQLite)
     - None
   * - ``POSTGRES_DB``
     - Database name
     - ``magpie``
   * - ``POSTGRES_USER``
     - Database user
     - ``magpie``
   * - ``POSTGRES_PASSWORD``
     - Database password
     - ``magpie``
   * - ``POSTGRES_PORT``
     - Database port
     - ``5432``

Celery
------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``CELERY_BROKER_URL``
     - Message broker URL (Redis or RabbitMQ)
     - None

Metrics (Graphite)
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``CARBON_SERVER_IP``
     - Graphite Carbon server IP
     - None
   * - ``CARBON_PICKLE_PORT``
     - Carbon pickle port
     - ``2004``
   * - ``NAMESPACE_ROOT``
     - Root namespace for metrics
     - ``default``
   * - ``METRIC_NAMESPACE``
     - Metric namespace
     - ``dev``

Bootstrap
---------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``DJANGO_SUPERUSER_USERNAME``
     - Initial admin username
     - ``admin``
   * - ``DJANGO_SUPERUSER_EMAIL``
     - Initial admin email
     - ``admin@example.com``
   * - ``DJANGO_SUPERUSER_PASSWORD``
     - Initial admin password (required for creation)
     - None

Container Metadata
------------------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Variable
     - Purpose
     - Default
   * - ``IMAGE_VERSION``
     - Image version (shown in ``/healthz``)
     - ``Unknown``
   * - ``CONTAINER_IMAGE``
     - Container image name (shown in ``/healthz``)
     - ``Unknown``
   * - ``FLOWER_DOMAIN``
     - Flower dashboard domain (shown on index page)
     - ``localhost:5555``

Endpoints
=========

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Path
     - Method
     - Description
   * - ``/``
     - GET
     - Site map with links to admin, API docs, and Flower
   * - ``/health``
     - GET
     - Simple health check — returns ``OK`` (plain text)
   * - ``/healthz``
     - GET
     - Detailed health check — returns JSON with version info
   * - ``/admin/``
     - GET
     - Django Admin (Unfold theme)
   * - ``/api/endpoints/``
     - CRUD
     - Endpoint management API
   * - ``/api/resolvers/``
     - CRUD
     - DNS resolver management API
   * - ``/api/resolver-lists/``
     - CRUD
     - DNS resolver list management API
   * - ``/api/scripts/``
     - CRUD
     - Script configuration management API
   * - ``/api/``
     - GET
     - Swagger UI
   * - ``/redoc/``
     - GET
     - ReDoc API documentation

Metrics Format
==============

Magpie posts metrics to Graphite in the following path structure:

.. code-block:: text

   {namespace}.{app_name}.mnemonic.{endpoint_mnemonic}.{metric_name}
   {namespace}.{app_name}.hostname.{hostname}.{metric_name}

Tagged metrics (when metadata is configured):

.. code-block:: text

   {namespace}.{app_name}.mnemonic.{endpoint_mnemonic}.{metric_name};tag1=val1;tag2=val2

Counters
--------

Every canary check records these counters:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Counter
     - Meaning
   * - ``requests``
     - Number of check attempts
   * - ``responses``
     - Successful responses
   * - ``errors``
     - Expected errors (bad status code, unhealthy response)
   * - ``exceptions``
     - Unexpected exceptions (timeouts, connection failures)

Check-Specific Attributes
-------------------------

**HTTP Health Check:** ``response_time``, ``response_time_ms``, ``status_code``, ``text``, ``request_time``, ``request_time_ms``, ``version``

**TLS Check:** ``response_time``, ``response_time_ms``, ``days_until_expiration``, ``expires_today``, ``is_valid``

**DNS Check:** ``response_time``, ``response_time_ms``, ``truncated``, ``rcode``, ``result``

Managing Endpoints
==================

Endpoints are managed through the Django Admin at ``/admin/``. Each endpoint can be configured with:

- **Mnemonic** — unique identifier used in metric paths
- **Hostname** and **port** — target server
- **Environment** — used for metric namespace grouping (e.g., ``prod``, ``staging``, ``dev``)
- **Health check settings** — scheme, path, expected status code, JSON response validation
- **TLS check** — enable/disable certificate monitoring
- **DNS check** — enable/disable with assigned resolver list
- **Timeouts** — configurable connect and read timeouts
- **Ignore flag** — temporarily disable an endpoint without deleting it

Canary task schedules are configured through Celery Beat in the Django Admin under **Periodic Tasks**.

Security
========

- See `SECURITY.md <SECURITY.md>`_ for vulnerability reporting guidelines
- All releases are signed with `Sigstore <https://www.sigstore.dev/>`_
- `CodeQL scanning <https://github.com/kuhl-haus/kuhl-haus-magpie/actions/workflows/github-code-scanning/codeql/>`_ runs on every push
- `Dependabot <https://github.com/kuhl-haus/kuhl-haus-magpie/security/dependabot>`_ monitors pip and Docker dependencies

Contributing
============

See `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ for development guidelines.

License
=======

This project is licensed under the terms of the `LICENSE.txt <LICENSE.txt>`_ file.

Note
====

This project was set up using `PyScaffold <https://pyscaffold.org/>`_ 4.6.
