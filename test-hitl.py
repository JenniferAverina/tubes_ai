
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import AgentState
from graph import apply_patch_node


# Graph khusus untuk menguji HITL
builder = StateGraph(AgentState)

builder.add_node("apply_patch", apply_patch_node)

builder.add_edge(START, "apply_patch")
builder.add_edge("apply_patch", END)

test_graph = builder.compile(
    checkpointer=MemorySaver(),
    interrupt_before=["apply_patch"]
)


# State pengujian
initial_state = {
    "file_path": "workspace/hitl_test.py",
    "fixed_code": 'print("FIXED CODE")',
    "approval": None,
    "patch_applied": False
}

config = {
    "configurable": {
        "thread_id": "hitl-test-001"
    }
}


# STEP 1: Jalankan sampai interrupt
print("\n========== STEP 1: WAITING FOR APPROVAL ==========")

test_graph.invoke(initial_state, config=config)

snapshot = test_graph.get_state(config)

print("Next node:", snapshot.next)
print("File belum boleh berubah.")


# STEP 2: Berikan approval
print("\n========== STEP 2: HUMAN APPROVAL ==========")

test_graph.update_state(
    config,
    {"approval": True}
)


# STEP 3: Resume workflow
print("\n========== STEP 3: RESUME GRAPH ==========")

result = test_graph.invoke(None, config=config)

print("Patch applied:", result.get("patch_applied"))
print("Patch result:", result.get("patch_result"))


# STEP 4: Periksa isi file
print("\n========== STEP 4: CHECK FILE ==========")

content = Path("workspace/hitl_test.py").read_text(
    encoding="utf-8"
)

print(content)
