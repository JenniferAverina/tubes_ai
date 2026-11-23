
from datetime import datetime


def log_trace(
    agent: str,
    thought: str,
    action: str,
    observation: str
) -> dict:

    """
    Record Thought, Action, Observation (TAO)
    for each agent execution.
    """

    entry = {
        "agent": agent,
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "thought": thought,
        "action": action,
        "observation": observation
    }

    print("\n==========================================")
    print(f" AGENT: {agent.upper()}")
    print("==========================================")

    print("\n[THOUGHT]")
    print(thought)

    print("\n[ACTION]")
    print(action)

    print("\n[OBSERVATION]")
    print(observation)

    print("==========================================")

    return entry


def display_trace(react_trace: list):

    print("\n========== COMPLETE REACT TRACE ==========")

    if not react_trace:
        print("No trace recorded.")
        return

    for index, entry in enumerate(react_trace, start=1):

        print(f"\n========== TRACE {index} ==========")

        print("Agent:", entry.get("agent"))
        print("Timestamp:", entry.get("timestamp"))

        print("\n[THOUGHT]")
        print(entry.get("thought"))

        print("\n[ACTION]")
        print(entry.get("action"))

        print("\n[OBSERVATION]")
        print(entry.get("observation"))

    print("\nTotal TAO entries:", len(react_trace))
    print("==========================================")
