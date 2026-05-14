import logging
from logging.handlers import RotatingFileHandler
from config import Config


def setup_logger(app):
    log_path = Config.LOG_PATH
    handler = RotatingFileHandler(
        log_path,
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    handler.setFormatter(formatter)

    app.logger.setLevel(logging.INFO)
    app.logger.addHandler(handler)

    return app.logger


def log_event(app_logger, event_name, level="info"):
    if level == "info":
        app_logger.info(f"Событие {event_name} зафиксировано.")
    else:
        app_logger.warning(f"Внимание {event_name} требует проверки.")