from logging import Logger, getLogger, StreamHandler, FileHandler, Formatter
from pathlib import Path


def get_logger(log_level: str, application_name: str = None, log_directory: str = None) -> Logger:
    application_name = __name__ if application_name is None else application_name
    logger: Logger = getLogger(application_name)
    logger.setLevel(log_level)
    logging_template = '{' \
        '"timestamp": "%(asctime)s", ' \
        '"filename": "%(filename)s", ' \
        '"function": "%(funcName)s", ' \
        '"line": "%(lineno)d", ' \
        '"level": "%(levelname)s", ' \
        '"pid": "%(process)d", ' \
        '"thr": "%(thread)d", ' \
        '"message": "%(message)s", ' \
        '}'
    log_formatter = Formatter(logging_template)

    # Stream Handler (console)
    stream_handler = StreamHandler()
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

    # File Handler
    if log_directory is not None or "":
        Path(log_directory).mkdir(parents=True, exist_ok=True)
        file_handler = FileHandler("{0}/{1}.log".format(log_directory, application_name))
        file_handler.setLevel(log_level)
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)

    return logger
