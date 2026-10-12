"""
==============================================================================
FILE HISTORY CARD
------------------------------------------------------------------------------
File:           logger.py
Author:         Asif Zaman
Created:        2026-10-12
Responsibility: Daily-rotating activity logger for the automation framework.
                Maintains date-stamped log files (logs/activity_YYYY-MM-DD.log)
                tracking every event, login attempt, scheduler trigger, CAPTCHA
                solution, and error with precise timestamps.
==============================================================================
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional


LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)


class DailyFileHandler(logging.Handler):
    """
    Custom handler that writes to logs/activity_YYYY-MM-DD.log.
    Automatically rotates to a new file when the date changes at midnight,
    avoiding file-lock issues on Windows.
    """
    def __init__(self, log_dir: str):
        super().__init__()
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.current_date = None
        self.file_stream = None

    def emit(self, record):
        try:
            today_str = datetime.now().strftime("%Y-%m-%d")
            if today_str != self.current_date:
                if self.file_stream:
                    try:
                        self.file_stream.close()
                    except Exception:
                        pass
                self.current_date = today_str
                log_path = os.path.join(self.log_dir, f"activity_{today_str}.log")
                self.file_stream = open(log_path, "a", encoding="utf-8")

            msg = self.format(record)
            self.file_stream.write(msg + "\n")
            self.file_stream.flush()
        except Exception:
            self.handleError(record)

    def close(self):
        if self.file_stream:
            try:
                self.file_stream.close()
            except Exception:
                pass
        super().close()


def get_logger(name: str = "automation") -> logging.Logger:
    """
    Returns a configured logger instance that writes to both the console
    and the date-stamped daily log file in logs/activity_YYYY-MM-DD.log.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    log_format = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Daily Rotating File Handler
    file_handler = DailyFileHandler(LOG_DIR)
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # 2. Console (Stdout) Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    logger.propagate = False
    return logger


# Global default logger instance for easy plug-and-play imports
logger = get_logger("automation")


def log_activity(message: str, level: str = "INFO"):
    """
    Helper function to log an activity with timestamp to the daily log file and console.
    """
    lvl = level.upper()
    if lvl == "ERROR":
        logger.error(message)
    elif lvl == "WARNING":
        logger.warning(message)
    elif lvl == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)
