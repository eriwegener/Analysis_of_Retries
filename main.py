from experiments.experimentDeadlock import start_deadlocks
from analysis.analysisDeadlock import start_analysis
from experiments.experimentSerialization import start_serialization
from experiments.experimentTimeout import start_timeout

def main():
    #start_deadlocks()
    #start_serialization()
    #start_timeout()
    start_analysis()

if __name__ == "__main__":
    main()
