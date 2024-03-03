import logging
import os
import pytest

from pysrc.services.logging_level_service import LoggingLevelService

# pytest tests/test_logging_level_service.py


def test_level():
    level = LoggingLevelService.get_level()
    assert level in [
        0,
        10,
        20,
        30,
        40,
        50,
    ]  # notset, debug, info, warning, error, critical
