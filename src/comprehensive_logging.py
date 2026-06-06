# RuneTarot — Comprehensive Logging System
# Fault-tolerant logging for all subsystems

"""
Comprehensive logging for RuneTarot.
All subsystems log through this module — never use print().
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

from src.utils import get_project_root


def setup_logging(
    level: str = "WARNING",
    log_file: Optional[str] = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """
    Set up the RuneTarot logging system.
    
    Creates a logger that writes to both console (stderr) and optionally to a file.
    Uses rotating file handler to prevent log files from growing unbounded.
    
    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name. If None, only console logging.
        max_bytes: Maximum log file size before rotation.
        backup_count: Number of rotated log files to keep.
    
    Returns:
        The configured root logger for RuneTarot.
    """
    # Get or create the logger
    logger = logging.getLogger("runetarot")
    
    # Avoid duplicate handlers on re-initialization
    if logger.handlers:
        return logger
    
    # Parse log level
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    logger.setLevel(numeric_level)
    
    # Create formatter — includes timestamp, module, level, message
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(name)s.%(module)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler — write to stderr so it doesn't interfere with Rich/Textual output
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional) — with rotation
    if log_file:
        try:
            from logging.handlers import RotatingFileHandler
            
            log_path = get_project_root() / log_file
            file_handler = RotatingFileHandler(
                str(log_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")
    
    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.
    
    Usage:
        logger = get_logger("deck")
        logger.info("Shuffling deck...")
    """
    return logging.getLogger(f"runetarot.{module_name}")
