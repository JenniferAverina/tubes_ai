
# Automated Code Debugger & Bug Finder

An Agentic AI-based Python debugging system that detects programming errors, retrieves relevant debugging knowledge, generates code fixes, and validates the proposed solution using multiple AI agents.

The system uses LangChain, LangGraph, Ollama, and ChromaDB to implement an autonomous debugging workflow.

---

## 1. Project Overview

Automated Code Debugger is designed to help identify and fix common Python programming errors.

The user provides Python source code directly inside `main.py`. The system then analyzes the code, identifies potential errors, searches for relevant debugging knowledge, generates a possible fix, and validates the corrected code.

Before applying the proposed fix, the system requests human approval.

### Main Features

- Automated Python error detection
- ReAct Diagnostic Loop
- Agentic Retrieval-Augmented Generation (RAG)
- Automatic query rewriting
- Supervisor-Worker multi-agent architecture
- Code fix generation
- Automatic code validation
- Human-in-the-Loop approval
- Debug trace logging

---

## 2. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| LangChain | LLM integration |
| LangGraph | Multi-agent workflow orchestration |
| Ollama | Local LLM execution |
| Qwen 2.5 7B | AI reasoning and code generation |
| ChromaDB | Vector database |
| nomic-embed-text | Text embedding model |

---

## 3. Project Structure

```text
tubes_ai/
│
├── agents/
│   ├── syntax_checker.py
│   ├── supervisor.py
│   ├── rag_specialist.py
│   └── code_fixer.py
│
├── tools/
│   ├── syntax_tool.py
│   ├── execution_tool.py
│   └── trace_logger.py
│
├── knowledge_base/
│   ├── syntax_errors.txt
│   ├── runtime_errors.txt
│   └── debugging_guide.txt
│
├── workspace/
│   ├── buggy_code.py
│   └── fixed_code.py
│
├── chroma_db/
│
├── state.py
├── graph.py
├── main.py
├── test_case.py
└── README.md
```

---

## 4. Installation

### Requirements

- Python 3.10 or newer
- Ollama
- Git (optional)

### Step 1: Clone or Download the Project

Open the project directory in Visual Studio Code.

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install langchain langchain-community langchain-ollama langgraph chromadb
```

Install any additional dependencies used by the project.

### Step 4: Install Ollama Models

Download the Qwen model:

```bash
ollama pull qwen2.5:7b
```

Download the embedding model:

```bash
ollama pull nomic-embed-text
```

Make sure Ollama is running before executing the project.

---

## 5. How to Use

### Step 1: Open main.py

The source code to be analyzed is written directly inside the `SOURCE_CODE` variable.

Example:

```python
SOURCE_CODE = """
x = 10
y = 0

print(x / y)
"""
```

This example contains a ZeroDivisionError.

### Step 2: Run the Program

Execute:

```bash
python main.py
```

### Step 3: Automated Debugging

The system automatically:

1. Analyzes the provided source code.
2. Detects syntax or runtime errors.
3. Searches the knowledge base for relevant debugging information.
4. Rewrites the search query if relevant knowledge cannot be found.
5. Generates a proposed code fix.
6. Validates the generated code.
7. Requests human approval before applying the patch.

### Step 4: Human Approval

The system pauses before applying the proposed patch.

The user can approve or reject the proposed modification.

- Approve: The corrected code is applied to the target file.
- Reject: The original code remains unchanged.

---

## 6. Multi-Agent Architecture

The project uses a Supervisor-Worker architecture.

### Syntax Checker Agent

Responsible for:

- Checking Python syntax using AST.
- Executing code to detect runtime errors.
- Identifying error types and error messages.

### Supervisor Agent

Responsible for:

- Managing the debugging workflow.
- Deciding which agent should execute next.
- Routing between the Syntax Checker, RAG Specialist, and Code Fixer.
- Managing retry attempts.

### RAG Specialist Agent

Responsible for:

- Searching the debugging knowledge base.
- Retrieving relevant error documentation.
- Evaluating retrieval relevance.
- Rewriting queries when relevant information is not found.

### Code Fixer Agent

Responsible for:

- Analyzing the detected error.
- Using retrieved debugging knowledge.
- Generating corrected Python code.
- Saving the proposed fix.

---

## 7. ReAct Diagnostic Loop

The system implements the ReAct pattern:

**Thought → Action → Observation**

### Thought

The agent determines what action should be performed.

### Action

The agent selects and executes an available tool.

### Observation

The agent receives and evaluates the tool result.

This process continues until the debugging workflow reaches its next stage.

The system also records the execution trace for debugging and demonstration purposes.

---

## 8. Agentic RAG with Self-Correction

The RAG Specialist uses ChromaDB to retrieve relevant debugging information.

### Retrieval Process

1. Receive the detected error and its context.
2. Search the knowledge base.
3. Evaluate the similarity distance of retrieved documents.
4. If relevant documents are found, provide them to the Code Fixer.
5. If no relevant documents are found, generate a rewritten query.
6. Retry retrieval using the rewritten query.
7. If the retry limit is reached, the Supervisor can route directly to the Code Fixer.

This mechanism allows the system to recover from unsuccessful knowledge retrieval attempts.

---

## 9. Code Validation

After generating a proposed fix, the system validates the output.

Validation includes:

- Checking whether generated code is empty.
- Checking Python syntax using AST.
- Executing the generated code.
- Detecting remaining errors.
- Applying a timeout to prevent indefinite execution.

If validation fails, the workflow does not proceed to patch approval.

---

## 10. Human-in-the-Loop

The system uses LangGraph's interrupt mechanism and MemorySaver to pause the workflow before applying modifications.

The proposed patch must be approved by the user.

This prevents the system from automatically modifying the original source code without human confirmation.

---

## 11. Demo and Debug Modes

The project provides two execution modes.

### Demo Mode

```python
DEBUG_MODE = False
```

Displays a simplified debugging result, suitable for presentations and live demonstrations.

### Debug Mode

```python
DEBUG_MODE = True
```

Displays detailed execution logs, including the ReAct Thought, Action, and Observation trace.

---

## 12. Knowledge Base

The debugging knowledge base is stored in the `knowledge_base/` directory.

| File | Description |
|---|---|
| syntax_errors.txt | Python syntax error information |
| runtime_errors.txt | Common runtime error information |
| debugging_guide.txt | General debugging techniques |

The documents are embedded and stored in ChromaDB for semantic retrieval.

If the knowledge base changes, rebuild or update the ChromaDB collection using the project's indexing process.

---

## 13. Example Errors

The system can be tested using different Python errors by changing `SOURCE_CODE` in `main.py`.

Examples include:

- ZeroDivisionError
- IndexError
- KeyError
- AttributeError
- SyntaxError

The `test_case.py` file may also be used for internal testing and development.

---

## 14. Important Notes

- The source code is configured directly inside `main.py`.
- No terminal input is required.
- Ollama must be running before executing the system.
- The required Ollama models must already be downloaded.
- The generated code should be reviewed before approval.
- Code execution should be performed in a controlled environment.

---

## 15. Project Objective

This project demonstrates how Agentic AI can be used to automate software debugging through reasoning, tool execution, knowledge retrieval, multi-agent collaboration, code generation, validation, and human supervision.
```

## 3. Cara menjalankan

```powershell
# Aktifkan virtual environment
.venv\Scripts\Activate.ps1

# Pastikan Ollama aktif
ollama list

# Jalankan debugger
python main.py
```

**Penting:** Karena `main.py` di atas adalah template, saya perlu melihat `main.py`, `state.py`, dan `graph.py` versi terakhirmu untuk memastikan nama state dan mekanisme Human Approval benar-benar cocok. Dengan begitu, saya bisa membuat versi final yang bisa langsung dijalankan tanpa merusak implementasi yang sudah selesai.