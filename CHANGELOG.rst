=========
Changelog
=========
Version 0.5.11 (2026-06-27)
===========================

- `a93a38d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/a93a38d>`_ Chore: bump codecov/codecov-action from v5.5.2 to v7 (#27)

  v7 runs on Node 24, resolving the Node 20 deprecation warning and

  the GPG signature verification failure seen in the v0.5.10 release

  build.


Version 0.5.10 (2026-06-27)
===========================

- `01a73bf <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/01a73bf>`_ Version 0.5.10 (2026-06-27)

  Add CHANGELOG entry for v0.5.10 (2026-06-27). Documents a fix exposing the dns_resolver_list on EndpointModelSerializer (use SlugRelatedField with slug_field='name' so resolver lists are referenced by name) and notes added serializer tests covering read/write paths (resolver name present, null when absent, valid/invalid write cases) and an assertion that the field is present in the existing serializer field test. References commit a9e750d.

- `a9e750d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/a9e750d>`_ Fix: expose dns_resolver_list in EndpointModel API (#26)

  * Fix: expose dns_resolver_list in EndpointModel API

  The dns_resolver_list ForeignKey exists on EndpointModel but was

  missing from EndpointModelSerializer, making it impossible to set

  or read via the REST API.

  Use SlugRelatedField with slug_field='name' so the resolver list

  is referenced by name (e.g. "default") in API requests and

  responses, consistent with the DnsResolverList model's natural

  identifier.

  * Test: add serializer tests for dns_resolver_list field

  Cover the four cases Bishop identified:

  - Read path: resolver list name appears as slug in serialized output

  - Read path: null when no resolver list is assigned

  - Write path: valid resolver list name deserializes to FK instance

  - Write path: invalid resolver list name fails validation

  Also assert dns_resolver_list is present (and null) in the existing

  test_endpoint_model_serializer_fields test.


Version 0.5.9 (2026-05-04)
==========================

- `8367059 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/8367059>`_ Version 0.5.9 (2026-05-04)
- `ec081af <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/ec081af>`_ feat: add update-changelog.sh script (#25)

  Generates CHANGELOG.rst from git tags and commits. Ported from

  kuhl-haus-mdp-app with credential-stripping fix for HTTPS remote URLs

  (strips embedded tokens before building commit links).

- `7ea2248 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/7ea2248>`_ Record API version in metrics.meta

  Store the raw version string from JSON responses into metrics.meta when the endpoint's version_key is present. This adds metrics.meta assignment in the HTTP health-check handler and updates tests to initialize metrics.meta and assert the version is saved there. Helps preserve the original version string for metadata/debugging while continuing to convert it to a numeric version for metrics.

- `90b3360 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/90b3360>`_ Update sphinx requirement from >=3.2.1 to >=9.1.0 (#24)

  Updates the requirements on [sphinx](https://github.com/sphinx-doc/sphinx) to permit the latest version.

  - [Release notes](https://github.com/sphinx-doc/sphinx/releases)

  - [Changelog](https://github.com/sphinx-doc/sphinx/blob/master/CHANGES.rst)

  - [Commits](https://github.com/sphinx-doc/sphinx/compare/v3.2.1...v9.1.0)

  ---

  updated-dependencies:

  - dependency-name: sphinx

  dependency-version: 9.1.0

  dependency-type: direct:production

  ...


Version 0.5.8 (2026-03-11)
==========================

- `96c553b <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/96c553b>`_ test: raise coverage to 99% with correctness assertions (issue #21) (#23)

  - Add bootstrap.py to coverage omit list in pyproject.toml

  - Add per-endpoint exception handler tests for all three canary tasks

  (http_health_check, tls_check, dns_check) verifying exception is caught,

  logger.exception is called, and task returns success

  - Upgrade 5 existing canary task tests with call assertions (ep arg,

  not-called guards)

  - Add health.py version fallback test covering the except block at import time

  - Add dns_check.py single-resolver coercion test covering line 17

  - Create tests/web/test_settings.py covering MAGPIE_DOMAIN, DISABLE_HTTPS,

  and POSTGRES_HOST conditional blocks

  - Add response body isinstance assertion to endpoint list test

  Result: 99.6% line coverage, 100% branch coverage (207 tests, all passing)

  Co-authored-by: Tom Pounders <git@oldschool.engineer>

- `2beeb4b <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/2beeb4b>`_ fix: remove dead code from canary_tasks and consolidate setup error handling (#22)

  Two unreachable code patterns were found in all three task functions:

  1. EndpointModel.objects.filter() was wrapped in 'except ObjectDoesNotExist'.

  QuerySet.filter() never raises ObjectDoesNotExist (only .get() does) —

  the except blocks could never execute. Fix: move the filter() call into

  the existing CarbonPoster try block so any unexpected DB exception is

  still caught.

  2. 'if ep.ignore: continue' guard inside a loop filtered with ignore=False.

  The queryset already excludes ignored endpoints, making the guard

  structurally unreachable. Fix: removed.

  Exception message updated from 'instantiating CarbonPoster' to

  'during task setup' to accurately reflect the broader scope of the block.

  Test updated to assert on the new error message.

  Coverage: 93% (up from 91%), 198 tests passing.

  Related: #21


Version 0.5.7 (2026-03-11)
==========================

- `325c3d0 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/325c3d0>`_ test: raise coverage to 91% and add missing migration (issue #18) (#20)

  Add Django layer tests to cover previously untested modules:

  - tests/test_env.py: canary/env.py and metrics/env.py defaults + overrides

  - tests/web/test_health.py: HTTP and JSON health endpoints

  - tests/web/test_context_processors.py: version_info and domain_info with cache

  - tests/web/test_celery.py: Celery app configuration

  - tests/endpoints/test_serializers.py: all four DRF ModelSerializers

  - tests/endpoints/test_api_views.py: all four ModelViewSets + custom action

  - tests/endpoints/test_models.py: model __str__, url property, field coverage

  - tests/canary_tasks/test_tasks.py: all three Celery tasks (happy path + empty)

  - tests/metrics/test_metrics_gaps.py: Metrics.log_metrics exception handler

  Also adds missing migration for EndpointModel.environment field (field

  existed in model but was absent from migrations — pre-existing gap).

  Updates pyproject.toml to omit infrastructure entry points and migrations

  from coverage measurement for a more honest denominator.

  Result: 198 tests passing, 91% coverage (up from 56%).

  Closes #18

- `5d2e37a <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/5d2e37a>`_ chore: add AGENTS.md stub and fix CLAUDE.md title (#17)

  - Add AGENTS.md pointing to CLAUDE.md as the canonical agent instructions file

  - Fix CLAUDE.md title (was incorrectly titled AGENTS.md)


Version 0.5.6 (2026-03-11)
==========================

- `b0a10e0 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/b0a10e0>`_ chore: restrict build-docker job to mainline branch and v* tags (#16)

  Docker images should only be built and pushed to GHCR when code lands

  on mainline — either via a direct push (squash-merged PRs) or a v*

  tagged release commit. PRs from feature branches will continue to run

  build-and-test for CI validation but skip the Docker build/push.

  Issue #15


Version 0.5.5 (2026-03-11)
==========================

- `aa1a610 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/aa1a610>`_ chore: upgrade GHA actions to Node.js 24 compatible versions (#14)

  GitHub is deprecating Node.js 20 on Actions runners starting June 2,

  2026. Update all affected actions to their latest Node.js 24 compatible

  versions:

  - actions/checkout: v4 -> v6

  - actions/setup-python: v5 -> v6

  - actions/upload-artifact: v4 -> v7

  - actions/download-artifact: v4 -> v8

  - docker/setup-buildx-action: v3 -> v4

  - docker/login-action: v3 -> v4

  - docker/build-push-action: v5 -> v7

  - sigstore/gh-action-sigstore-python: v3.0.0 -> v3.2.0

  - codecov/codecov-action: v5 -> v5.5.2

  Closes #13


Version 0.5.4 (2026-03-11)
==========================

- `76e15b5 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/76e15b5>`_ fix: build package before pdm install to prevent dirty version suffix (#12)

  pdm install regenerates pdm.lock (a tracked file), making the working

  tree dirty at build time. pdm-backend appends +d<date> to the version

  when the tree is dirty, producing local version identifiers like

  0.5.3+d20260305 that PyPI rejects with a 400 Bad Request.

  Fix: move 'pdm build' before 'pdm install' so the build runs on a

  clean working tree and produces the clean version string.

- `c7acef3 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/c7acef3>`_ Disable local version in setuptools_scm

  Add [tool.setuptools_scm] with local_scheme = "no-local-version" to pyproject.toml to prevent appending local version identifiers (e.g. +dirty or build metadata). This ensures package versioning is compatible with PyPI.


Version 0.5.3 (2026-03-05)
==========================

- `475b533 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/475b533>`_ Normalize ASCII architecture diagrams

  Reformat ASCII architecture diagrams in CLAUDE.md and README.rst for consistent box widths, alignment, and spacing.

- `567f117 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/567f117>`_ rename: AGENTS.md → CLAUDE.md (#10)

  Standardizing on CLAUDE.md as the Claude Code convention over the

  generic AGENTS.md convention. Content unchanged.

  Co-authored-by: Tom Pounders <git@oldschool.engineer>

- `0cca79b <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/0cca79b>`_ chore: consolidate project config into pyproject.toml (#9)

  - Delete setup.py, setup.cfg, pytest.ini, .coveragerc (legacy PyScaffold artifacts)

  - Convert README.md to README.rst; delete README.md

  - pyproject.toml: switch to dynamic SCM versioning, update readme field,

  clean [project.urls], remove [tool.setuptools]/[tool.devpi.upload]/[tool.pyscaffold],

  merge pytest config from pytest.ini, migrate coverage config from .coveragerc,

  fix coverage source package name (bedrock_magpie -> kuhl_haus.magpie)

  - GHA workflow: replace grep-based version extraction with setuptools-scm

  Closes #8

  Co-authored-by: Tom Pounders <git@oldschool.engineer>

- `c6dc11e <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/c6dc11e>`_ feat: add AGENTS.md and rewrite README.md (#7)

  Add AGENTS.md — comprehensive instructions for AI agents assisting with

  code maintenance: architecture overview, repo layout, development setup,

  common maintenance tasks, environment variable reference, coding standards,

  and known technical debt inventory.

  Rewrite README.md — replace placeholder with full user documentation:

  architecture diagram, tech stack, quick start (PyPI/Docker/dev), complete

  environment variable reference, API endpoint table, metrics format docs,

  endpoint management guide, and security/contributing links.

  Co-authored-by: Tom Pounders <git@oldschool.engineer>


Version 0.5.2 (2026-01-23)
==========================

- `29c147c <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/29c147c>`_ Version 0.5.2 - dependency upgrade

  No code changes needed.

- `819bf6d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/819bf6d>`_ Update requirements.txt

Version 0.5.1 (2025-12-31)
==========================

- `0a89842 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/0a89842>`_ Use version_to_int for HTTP health check
- `3148f20 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/3148f20>`_ Ignore compose.yaml

Version 0.5.0 (2025-12-27)
==========================

- `d59ddf4 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/d59ddf4>`_ [version 0.5.0] Removed Langflow chat widget

Version 0.4.0 (2025-07-06)
==========================

- `d41c5e9 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/d41c5e9>`_ [version 0.4.0] Site map home page with chatbot widget

  Removed obsolete endpoints UI and replaced with a site map + langflow chat widget.


Version 0.3.2 (2025-06-19)
==========================

- `fd59a3c <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/fd59a3c>`_ [version 0.3.2] Added health check

Version 0.3.1 (2025-06-19)
==========================

- `4a6d27a <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/4a6d27a>`_ [version 0.3.1] Added environment attribute to endpoint models.

  Removed unused and overly complicated canary script and its associated modules.

- `f4afc71 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f4afc71>`_ [version 0.2.6] Replaced shared_task decorator with app.task

  This is why the the tasks weren't auto-discovered.

  https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html#using-the-shared-task-decorator


Version 0.2.5 (2025-05-21)
==========================

- `fa436a9 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/fa436a9>`_ [version 0.2.5] Sortable & filterable endpoint list
- `3dbd22d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/3dbd22d>`_ [version 0.2.4] Rendering hostname as URL in endpoint list

Version 0.2.3 (2025-05-20)
==========================

- `05282ea <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/05282ea>`_ [version 0.2.3] Default script_config_name matches function name.

  This should make it a little more intuitive setting up script configs.


Version 0.2.2 (2025-05-20)
==========================


Version 0.2.4 (2025-05-21)
==========================

- `3dbd22d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/3dbd22d>`_ [version 0.2.4] Rendering hostname as URL in endpoint list
- `05282ea <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/05282ea>`_ [version 0.2.3] Default script_config_name matches function name.

  This should make it a little more intuitive setting up script configs.

- `c897d94 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/c897d94>`_ [version 0.2.2] Lookup script config by name instead of by application name

Version 0.2.1 (2025-05-20)
==========================

- `794c388 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/794c388>`_ [version 0.2.1] Add carbon_server_ip to ScriptConfig display and search fields
- `f27d679 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f27d679>`_ Fixed column headers in endpoint list view

Version 0.2.0 (2025-05-20)
==========================

- `e80da2f <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/e80da2f>`_ [version 0.2.0] Created initial DB migration

Version 0.1.18 (2025-05-20)
===========================

- `22bc83f <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/22bc83f>`_ [version 0.1.18] Clean-up endpoint list display

Version 0.1.17 (2025-05-20)
===========================

- `b7fb908 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/b7fb908>`_ [version 0.1.17] Refactored script/carbon client config relationsip

Version 0.1.16 (2025-05-19)
===========================

- `c4571b5 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/c4571b5>`_ [version 0.1.16] Fixed celery beat integration

  https://unfoldadmin.com/docs/integrations/django-celery-beat/


Version 0.1.15 (2025-05-19)
===========================

- `7876935 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/7876935>`_ [version 0.1.15] Added Unfold theme for Admin
- `412f544 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/412f544>`_ CONFIG_API  no longer needed.

Version 0.1.14 (2025-05-19)
===========================

- `b1b37a0 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/b1b37a0>`_ [version 0.1.14] Added response_time attributes to DNS and TLS checks

Version 0.1.13 (2025-05-19)
===========================

- `f7a347e <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f7a347e>`_ [version 0.1.13] Bumping version
- `3e0d88d <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/3e0d88d>`_ Fixed DNS check
- `f2812e9 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f2812e9>`_ Missed in last commit
- `8d2a4d8 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/8d2a4d8>`_ Removed redundant models from Canary
- `ec23df4 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/ec23df4>`_ That was a little pre-mature.
- `9559b27 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/9559b27>`_ Revert "Removed explicit Celery Includes"

  This reverts commit 607b31bb5e95dbdccc02b20e803a376ebd092c3a.

- `607b31b <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/607b31b>`_ Removed explicit Celery Includes
- `f4fc1d7 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f4fc1d7>`_ [version 0.1.12] Consolidated related kuhl-haus packages

Version 0.1.11 (2025-05-18)
===========================

- `2c9aae7 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/2c9aae7>`_ [version 0.1.11] Added individual tasks for tls, dns, and http checks
- `7175356 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/7175356>`_ Remove version count from image tag

  IMAGE_TAG="${VERSION}-${COMMIT_SHORT}"


Version 0.1.10 (2025-05-08)
===========================

- `98b6431 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/98b6431>`_ [version 0.1.10] Added metric_namespace to result metadata.

Version 0.1.9 (2025-05-08)
==========================

- `4b46ef0 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/4b46ef0>`_ [version 0.1.9] Added namespace to ScriptConfig

  https://github.com/kuhl-haus/kuhl-haus-metrics/issues/18


Version 0.1.8 (2025-05-08)
==========================

- `00af163 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/00af163>`_ V0.1.8 Update endpoint model (#3)

  * Celery integration for scheduled tasks

  * Update publish-to-pypi.yml

  Build image on untagged builds.

  * Added Celery related services to compose file

  * Update pyproject.toml

  Removed redundant 'requests'

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

  * [version 0.1.5] Added basic canary task

  * Removed pop from list

  https://github.com/kuhl-haus/kuhl-haus-magpie/pull/2/#discussion_r2076614287

  https://github.com/kuhl-haus/kuhl-haus-magpie/pull/2/#discussion_r2076614292

  * [version 0.1.8] Update endpoint model

  * Replaced json_response boolean with response_format option

  * Added HTTP verbs and body

  * Added toggles for each type of canary check

  * Updated views and made Django db migration file

  ---------

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>


Version 0.1.7 (2025-05-08)
==========================

- `7a02521 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/7a02521>`_ [version 0.1.7] Update DB connection settings to mitigate "too many connections" errors

  'CONN_MAX_AGE': 0

  The development server creates a new thread for each request it handles, negating the effect of persistent connections. Don’t enable them during development.


Version 0.1.6 (2025-05-07)
==========================

- `dfd4db2 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/dfd4db2>`_ [version 0.1.6] Minor tweaks

  1. Added to the nav bar:

  * Flower Dashboard

  * Admin Site

  2. Override DATA_UPLOAD_MAX_NUMBER_FIELDS so it isn't such a PITA to delete a bunch of canary tasks from the db.


Version 0.1.5 (2025-05-06)
==========================

- `0110756 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/0110756>`_ v0.1.5 - Added a basic canary task (#2)

  * Celery integration for scheduled tasks

  * Update publish-to-pypi.yml

  Build image on untagged builds.

  * Added Celery related services to compose file

  * Update pyproject.toml

  Removed redundant 'requests'

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

  * [version 0.1.5] Added basic canary task

  * Removed pop from list

  https://github.com/kuhl-haus/kuhl-haus-magpie/pull/2/#discussion_r2076614287

  https://github.com/kuhl-haus/kuhl-haus-magpie/pull/2/#discussion_r2076614292

  ---------

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>


Version 0.1.4 (2025-05-05)
==========================

- `f32eea3 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/f32eea3>`_ [version 0.1.4] Celery integration for scheduled tasks (#1)

  * Celery integration for scheduled tasks

  * Update publish-to-pypi.yml

  Build image on untagged builds.

  * Added Celery related services to compose file

  * Update pyproject.toml

  Removed redundant 'requests'

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

  ---------

  Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

- `d7cea90 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/d7cea90>`_ Update SECURITY.md

Version 0.1.3 (2025-05-03)
==========================

- `77dcb17 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/77dcb17>`_ [version 0.1.3] Removed netcat dependency in docker-entrypoint.sh

  https://github.com/kuhl-haus/kuhl-haus-magpie/actions/runs/14814834510/job/41594081482#step:6:296


Version 0.1.2 (2025-05-03)
==========================

- `d06a404 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/d06a404>`_ No tests; no CI build

  https://github.com/kuhl-haus/kuhl-haus-magpie/actions/runs/14814236541/job/41592770466

- `9fa44e0 <https://github.com/kuhl-haus/kuhl-haus-magpie/commit/9fa44e0>`_ Initial commit - load kuhl-haus-canary configuration via API

  https://github.com/kuhl-haus/kuhl-haus-canary/issues/13


