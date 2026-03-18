import logging
import os

LOG_FILE = "app.log"

def init_logger():

    logging.basicConfig(

        level=logging.INFO,

        format="%(asctime)s | %(levelname)s | %(message)s",

        handlers=[

            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler()
            
        ]
    )

    logging.getLogger('werkzeug').setLevel(logging.ERROR)

def log_info(message: str):
    logging.info(message)

def log_error(message: str):
    logging.error(message)