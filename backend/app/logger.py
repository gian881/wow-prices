import logging
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(name)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )
)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(name)s - %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )
)
root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Get logger for a specific module"""
    return logging.getLogger(name)
