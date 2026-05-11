from experiments.experimentDeadlocks import start_deadlocks
from analysis.analysisDeadlock import start_analysis
from config.settings import LOG_PATH, BASE_DIR

def main():
    path = BASE_DIR + LOG_PATH
    #with open(path, "w"):
        #pass
    start_deadlocks()
    #start_analysis()

if __name__ == "__main__":
    main()
