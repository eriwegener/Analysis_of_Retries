RETRY_COUNT = [0, 1, 2, 3, 5]
RETRY_DELAY = [0, 0.01, 0.1, 0.5]
RETRY_STRATEGY = ["no_retry", "no_delay", "static_delay", "exponential_delay", "jitter_delay"]

CONCURRENCY = [2, 15, 75]
WORKLOAD = [500, 1000, 1500, 2000]
ITERATIONS = 3

LOG_PATH = "/logging/deadlocks/results.jsonl"
BASE_DIR = "/home/eric/Documents/idea-IU-252.26830.84/projects/Bachelorarbeit"

ENABLE_LOGGING = True