import logging
import os

from pythonjsonlogger import jsonlogger

LOG_LEVEL_RAW = os.getenv("LOG_LEVEL", "INFO")
LOG_LEVEL = getattr(logging, LOG_LEVEL_RAW.upper())
logging.basicConfig(level=LOG_LEVEL)


class CustomJsonFormatter(jsonlogger.JsonFormatter):

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(
            log_record,
            record,
            message_dict
        )
        log_record["level"] = log_record.get("level", record.levelname).upper()


def get_log_handler():
    log_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter(timestamp=True)
    log_handler.setFormatter(formatter)
    return log_handler
