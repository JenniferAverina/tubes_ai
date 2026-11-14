from state import AgentState

test_state: AgentState = {
    "source_code": "print('Hello')",
    "diagnosis": {
        "status": "SUCCESS"
    }
}

print(test_state)