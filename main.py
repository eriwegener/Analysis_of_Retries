from experiments.experimentDeadlock import start_deadlocks
from analysis.analysisDeadlock import start_analysis
from experiments.experimentSerialization import start_serialization
from experiments.experimentTimeout import start_timeout

def main():
    print("=== Deadlock ===")
    start_deadlocks()
    print("=== Serialization ===")
    start_serialization()
    print("=== Lock-Timeout ===")
    start_timeout()
    #start_analysis()

if __name__ == "__main__":
    main()
