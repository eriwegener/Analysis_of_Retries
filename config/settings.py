from pathlib import Path

RETRY_COUNT = [0, 1, 3, 5]
RETRY_DELAY = [0, 0.005, 0.01, 0.05, 0.1]
RETRY_STRATEGY = [0, 1, 2, 3]

CONCURRENCY = [2, 5, 7, 10, 20]
WORKLOAD = [500]
ITERATIONS = 5

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logging"
LOG_PATH_D = LOG_DIR / "results_deadlock.jsonl"
LOG_PATH_S = LOG_DIR / "results_serialization.jsonl"
LOG_PATH_T = LOG_DIR / "results_timeout.jsonl"
LOG_PATH_E = LOG_DIR / "error.jsonl"
LOG_PATH_TEST = LOG_DIR / "tests" / "result_test7.jsonl"

ENABLE_LOGGING = True
ENABLE_TEST = False