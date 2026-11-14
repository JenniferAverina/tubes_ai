from agents.syntax_checker import syntax_checker_node
state = {
    "source_code": """
x = 10
y = 0
print(x / y)
"""
}
result = syntax_checker_node(state)

print("\n=== SYNTAX RESULT ===")
print(result.get("syntax_result"))

print("\n=== EXECUTION RESULT ===")
print(result.get("execution_result"))

print("\n=== DIAGNOSIS ===")
print(result.get("diagnosis"))

print("\n=== REACT TRACE ===")
print(result.get("react_trace"))