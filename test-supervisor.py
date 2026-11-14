
from agents.supervisor import supervisor_node, supervisor_router

# Test 1: Program berhasil
state_success = {
    "diagnosis": {
        "status": "SUCCESS"
    }
}

result = supervisor_node(state_success)

print("=== TEST SUCCESS ===")
print(result)
print("Router:", supervisor_router(result))


# Test 2: Program mengalami error
state_error = {
    "diagnosis": {
        "status": "ERROR",
        "error_type": "ZeroDivisionError"
    }
}

result = supervisor_node(state_error)

print("\n=== TEST ERROR ===")
print(result)
print("Router:", supervisor_router(result))
