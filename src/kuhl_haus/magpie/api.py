import locale
import logging
import os
import sys
import traceback

import django
import uvicorn
from django.conf import settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from rich.logging import RichHandler

import kuhl_haus.magpie.web.wsgi as web_wsgi

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuhl_haus.magpie.web.settings')
django.setup()


# Setup Logger
rich_handler = RichHandler(rich_tracebacks=True)
rich_handler.setFormatter(fmt=logging.Formatter(fmt="%(name)s: %(message)s", datefmt="[%H:%M:%S.%f]"))
logging.basicConfig(handlers=[rich_handler])

logging.getLogger("uvicorn.error").setLevel(logging.INFO)

LOGGER = logging.getLogger("magpie")

app = web_wsgi.application

app.add_middleware(
    CORSMiddleware,
    # allow_origins=default_origins + custom_origins,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set Locale
locale.setlocale(locale.LC_ALL, "")


def main(*args):
    LOGGER.info("Service starting up... Hello!")
    try:
        msg = ("instantiate from python version %s executable %s, pid: %s" %
               (sys.version, sys.executable, str(os.getpid()),))
        msg = msg.replace("\n", " ")
        LOGGER.info(msg)

        #  Mount Django and Static Files
        app.mount("/server", web_wsgi.application, name="server")

        static_dir = settings.STATIC_ROOT
        if not os.path.exists(static_dir):
            os.mkdir(static_dir)
        app.mount(f"/static", StaticFiles(directory=static_dir), name=static_dir)

        LOGGER.info(
            "Listening on %s:%d",
            settings.SERVER_IP,
            settings.SERVER_PORT
        )

        uvicorn.run(
            "kuhl_haus.magpie.web.wsgi:application",
            host=settings.SERVER_IP,
            port=settings.SERVER_PORT,
            reload=True,
            access_log=True,
            log_level=logging.ERROR
        )
    except KeyboardInterrupt:
        LOGGER.info("Received interrupt, exiting")
    except Exception as e:
        print(f"Unhandled exception raised:{repr(e)}", file=sys.stderr)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(exc_type, exc_value, exc_traceback, limit=2, file=sys.stderr)
        LOGGER.error("Unhandled exception raised:%s", repr(e), exc_info=e, stack_info=True)
        raise
    finally:
        LOGGER.info("Service shutting down... Good-bye.")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[2:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m kuhl_haus.magpie.api
    #
    run()
