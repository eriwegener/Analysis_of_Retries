from experiments.experimentRunner import start_deadlocks, start_serialization, start_timeout
from analysis.analysis import start_analysis
from config.settings import LOG_PATH_D, LOG_PATH_S, LOG_PATH_T

def main():
    #print("=== Deadlock ===")
    #start_deadlocks()
    #print("=== Serialization ===")
    #start_serialization()
    #print("=== Lock-Timeout ===")
    #start_timeout()
    start_analysis(LOG_PATH_D)

if __name__ == "__main__":
    main()
