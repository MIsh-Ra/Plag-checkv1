import logging
from pythonjsonlogger import jsonlogger
from datetime import datetime, timezone

class AlethianJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.now(timezone.utc).isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(AlethianJsonFormatter('%(message)s'))
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)
    return logger

logger = setup_logging()
