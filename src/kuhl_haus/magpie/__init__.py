from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

from kuhl_haus.magpie.web import celery_app as celery
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# IMPORTANT: This is a work-around for the naming conflict created by Celery's configuration convention.
#
# If you have suggestions for a better way of handling this, please file an issue here:
# https://github.com/kuhl-haus/kuhl-haus-magpie/issues/new/choose
#
# More Info:
# Celery requires a package-level attribute named 'celery'.  However, if you put 'from celery...' in a file named
# celery.py, it results in a circular reference because the relative import conflicts with the absolute import.
# Adding `from __future__ import absolute_import` doesn't seem to have any effect.
#
# Reference: https://docs.celeryq.dev/en/stable/getting-started/next-steps.html#our-project
#
# Project layout:
# ```
# src/
#     proj/__init__.py
#         /celery.py
#         /tasks.py
# ```
#
#
# proj/celery.py
# ```
# from celery import Celery
#
# app = Celery('proj',
#              broker='amqp://',
#              backend='rpc://',
#              include=['proj.tasks'])
#
# # Optional configuration, see the application user guide.
# app.conf.update(
#     result_expires=3600,
# )
#
# if __name__ == '__main__':
#     app.start()
# ```
#
