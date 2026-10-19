"""Logging to stderr only — stdout is the MCP stdio channel and must stay clean."""
import logging
import os
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(h)
        logger.setLevel(os.environ.get("BIMHUB_LOG", "INFO").upper())
    return logger
