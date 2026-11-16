# test_member2.py
import os
import shutil
import json
from state import AgentState
from agents.rag_specialist import rag_specialist_node, PERSIST_DIR
from agents.code_fixer import code_fixer_node


def reset_chroma_db():
    """Removes old ChromaDB directory so updated .txt files are freshly embedded."""
    if os.path.exists(PERSIST_DIR):
        print(f"[Setup] Removing existing '{PERSIST_DIR}' to re-index knowledge_base/*.txt...")
        shutil.rmtree(PERSIST_DIR)


def print_state_summary(title: str, state: AgentState):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)
    print(f"Search Attempt   : {state.get('search_attempt')}")
    print(f"Rewritten Query  : {state.get('rewritten_query') or 'N/A (Initial Search)'}")
    
    kb_res = state.get("knowledge_result", "")
    kb_preview = kb_res[:200] + "..." if len(str(kb_res)) > 200 else kb_res
    print(f"Knowledge Result :\n{kb_preview}\n")
    
    if state.get("fixed_code"):
        print(f"Fix Attempts     : {state.get('fix_attempts')}")
        print("Generated Fixed Code:\n" + "-" * 40)
        print(state.get("fixed_code"))
        print("-" * 40)

    print("ReAct Trace Log:")
    print(json.dumps(state.get("react_trace", []), indent=2))


def run_tests():
    reset_chroma_db()

    # -------------------------------------------------------------------------
    # TEST 1: Runtime Error (ZeroDivisionError) -> RAG -> Code Fixer
    # -------------------------------------------------------------------------
    state_runtime: AgentState = {
        "source_code": (
            "def calculate_average(numbers):\n"
            "    total = sum(numbers)\n"
            "    return total / len(numbers)\n\n"
            "data = []\n"
            "print(calculate_average(data))"
        ),
        "diagnosis": {
            "status": "ERROR",
            "error_type": "ZeroDivisionError",
            "error_message": "division by zero",
            "line": 3
        },
        "search_attempt": 0,
        "fix_attempts": 0,
        "react_trace": []
    }

    print("\n>>> Running Test 1: Runtime Error (ZeroDivisionError)...")
    # Step 1: Run RAG Specialist
    rag_updates = rag_specialist_node(state_runtime)
    state_runtime.update(rag_updates)

    # Step 2: Run Code Fixer
    fixer_updates = code_fixer_node(state_runtime)
    state_runtime.update(fixer_updates)

    print_state_summary("TEST 1 RESULT: ZeroDivisionError Pipeline", state_runtime)

    # -------------------------------------------------------------------------
    # TEST 2: Syntax Error (Missing Colon) -> RAG -> Code Fixer
    # -------------------------------------------------------------------------
    state_syntax: AgentState = {
        "source_code": (
            "def greet(name)\n"
            "    print(f'Hello, {name}!')\n\n"
            "greet('Alice')"
        ),
        "diagnosis": {
            "status": "ERROR",
            "error_type": "SyntaxError",
            "error_message": "expected ':'",
            "line": 1,
            "column": 15,
            "source_line": "def greet(name)"
        },
        "search_attempt": 0,
        "fix_attempts": 0,
        "react_trace": []
    }

    print("\n>>> Running Test 2: Syntax Error (Missing Colon)...")
    state_syntax.update(rag_specialist_node(state_syntax))
    state_syntax.update(code_fixer_node(state_syntax))
    print_state_summary("TEST 2 RESULT: SyntaxError Pipeline", state_syntax)

    # -------------------------------------------------------------------------
    # TEST 3: Simulate NOT_FOUND -> Query Rewriting on Retry (search_attempt=1)
    # -------------------------------------------------------------------------
    state_rewrite: AgentState = {
        "source_code": "items = [1, 2, 3]\nprint(items[5])",
        "diagnosis": {
            "status": "ERROR",
            "error_type": "IndexError",
            "error_message": "list index out of range",
            "line": 2
        },
        "knowledge_result": "NOT_FOUND",
        "rewritten_query": "obscure initial query that failed",
        "search_attempt": 1,  # Simulates Supervisor routing back for retry #1
        "fix_attempts": 0,
        "react_trace": []
    }

    print("\n>>> Running Test 3: Query Rewriting (search_attempt = 1)...")
    state_rewrite.update(rag_specialist_node(state_rewrite))
    print_state_summary("TEST 3 RESULT: Query Rewrite Verification", state_rewrite)


if __name__ == "__main__":
    run_tests()