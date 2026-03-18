import time
from logging_config import init_logger, log_info

MAX_FAILED = 5
BLOCK_TIME = 1 * 60
RESET_TIME = 15 * 60

failed_attempts = {}  

def check_block(email):

    now = time.time()

    if email not in failed_attempts:
        return False, 0

    data = failed_attempts[email]

    if data.get("blocked_until", 0) > now:
        return True, int(data["blocked_until"] - now)

    return False, 0

def add_fail(email):

    now = time.time()

    if email not in failed_attempts:

        failed_attempts[email] = {
            "count": 1,
            "first_time": now,
            "blocked_until": 0
        }

        return

    data = failed_attempts[email]

    if now - data["first_time"] > RESET_TIME:

        failed_attempts[email] = {
            "count": 1,
            "first_time": now,
            "blocked_until": 0
        }

        return

    data["count"] += 1

    if data["count"] >= MAX_FAILED:

        log_info(f"Uzytkonik z mailem {email} zostal zablokowany na czas {now + BLOCK_TIME} po niudanej liczbie prob logowania: {MAX_FAILED}")

        data["blocked_until"] = now + BLOCK_TIME


def reset(email):

    if email in failed_attempts:

        log_info(f"Uzytkonik z mailem {email} zostal odblokowany do zalogowania sie")

        del failed_attempts[email]