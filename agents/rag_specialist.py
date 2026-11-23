import os

from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.documents import Document

from state import AgentState
from tools.trace_logger import log_trace


# ==========================================
# 1. INITIALIZE LOCAL MODELS
# ==========================================

embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)


# ==========================================
# 2. CONFIGURATION
# ==========================================

PERSIST_DIR = "./chroma_db"
KB_DIR = "./knowledge_base"

DISTANCE_THRESHOLD = 1.2


# ==========================================
# 3. LOAD KNOWLEDGE BASE
# ==========================================

def get_vectorstore() -> Chroma:

    print("\n========== LOAD KNOWLEDGE BASE ==========")

    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):

        print("Loading existing ChromaDB...")

        return Chroma(
            persist_directory=PERSIST_DIR,
            embedding_function=embeddings
        )

    docs = []

    kb_files = [
        "syntax_errors.txt",
        "runtime_errors.txt",
        "debugging_guide.txt"
    ]

    for filename in kb_files:

        filepath = os.path.join(KB_DIR, filename)

        if os.path.exists(filepath):

            print(f"Reading: {filename}")

            with open(filepath, "r", encoding="utf-8") as f:

                content = f.read()

                chunks = [
                    c.strip()
                    for c in content.split("---")
                    if c.strip()
                ]

                for chunk in chunks:

                    docs.append(
                        Document(
                            page_content=chunk,
                            metadata={"source": filename}
                        )
                    )

            print(f"Chunks loaded: {len(chunks)}")

        else:

            print(f"WARNING: {filename} not found!")

    if not docs:

        print("WARNING: No Knowledge Base documents found!")

        docs = [
            Document(
                page_content="Placeholder debugging entry",
                metadata={"source": "init"}
            )
        ]

    print("Total documents:", len(docs))
    print("Creating ChromaDB...")

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )

    print("ChromaDB successfully created.")

    return vectorstore


# ==========================================
# 4. RAG SPECIALIST NODE
# ==========================================

def rag_specialist_node(state: AgentState) -> dict:

    print("\n========== RAG SPECIALIST START ==========")

    diagnosis = state.get("diagnosis") or {}

    error_type = diagnosis.get("error_type", "UnknownError")
    error_message = diagnosis.get("error_message", "")
    source_line = diagnosis.get("source_line", "")

    attempt = state.get("search_attempt", 0)

    trace = list(state.get("react_trace", []))

    vectorstore = get_vectorstore()

    # ======================================
    # 5. QUERY FORMULATION / REWRITING
    # ======================================

    if attempt == 0:

        query = (
            f"Python {error_type}: "
            f"{error_message} {source_line}"
        ).strip()

        rewritten = ""

        thought_msg = (
            f"Initial KB search for {error_type}: '{query}'"
        )

        action_msg = "Formulate initial Knowledge Base search query."

    else:

        prev_query = (
            state.get("rewritten_query")
            or f"Python {error_type}: {error_message}"
        )

        rewrite_prompt = f"""
You are a Python debugging search assistant.

The previous search query:
{prev_query}

returned NOT_FOUND in our debugging knowledge base.

Error Type: {error_type}
Error Message: {error_message}

Rewrite the query into a broader semantic search query.

Focus on:
- The cause of this Python error.
- Common situations that trigger this error.
- Practical ways to prevent and fix it.

Output ONLY the search query.
"""

        print("\n[QUERY REWRITING] Asking Qwen to rewrite query...")

        rewritten = llm.invoke(rewrite_prompt).content.strip().strip('"')

        query = rewritten

        thought_msg = (
            f"Previous search returned NOT_FOUND. "
            f"Rewrote query to: '{rewritten}'"
        )

        action_msg = "Invoke Qwen to rewrite the previous search query."

    print("\n[RAG QUERY]")
    print(query)

    # Log query formulation / rewriting
    trace_entry = log_trace(
        agent="RAG_SPECIALIST",
        thought=thought_msg,
        action=action_msg,
        observation=f"Search query prepared: {query}"
    )

    trace.append(trace_entry)

    # ======================================
    # 6. VECTOR SEARCH
    # ======================================

    results = vectorstore.similarity_search_with_score(
        query,
        k=2
    )

    print("\n========== RAG SEARCH DEBUG ==========")
    print("Number of results:", len(results))

    for doc, score in results:

        print("\nSource:", doc.metadata.get("source"))
        print("Distance score:", score)
        print("Content:", doc.page_content[:300])

    # ======================================
    # 7. EVALUATE SEARCH RESULTS
    # ======================================

    if not results:

        knowledge_result = "NOT_FOUND"

        obs_msg = "No matching documents found."

    elif results[0][1] > DISTANCE_THRESHOLD:

        knowledge_result = "NOT_FOUND"

        obs_msg = (
            f"Best distance score {results[0][1]:.3f} "
            f"exceeded threshold {DISTANCE_THRESHOLD}."
        )

    else:

        knowledge_result = "\n\n".join(
            [
                f"[{doc.metadata.get('source')}]\n{doc.page_content}"
                for doc, score in results
            ]
        )

        obs_msg = (
            f"Found {len(results)} relevant solution(s). "
            f"Best distance score: {results[0][1]:.3f}."
        )

    print("\n[RAG RESULT]")

    print(
        "FOUND"
        if knowledge_result != "NOT_FOUND"
        else "NOT_FOUND"
    )

    # ======================================
    # 8. REACT TRACE: RETRIEVAL
    # ======================================

    trace_entry = log_trace(
        agent="RAG_SPECIALIST",
        thought=(
            "Evaluate the retrieved documents using their "
            "similarity distance scores and relevance threshold."
        ),
        action=(
            f"ChromaDB similarity_search_with_score("
            f"query='{query}', k=2)"
        ),
        observation=(
            f"Result: {'FOUND' if knowledge_result != 'NOT_FOUND' else 'NOT_FOUND'}. "
            f"{obs_msg}"
        )
    )

    trace.append(trace_entry)

    # ======================================
    # 9. RETURN UPDATED STATE
    # ======================================

    return {

        "knowledge_result": knowledge_result,

        "rewritten_query": rewritten,

        "search_attempt": attempt + 1,

        "react_trace": trace
    }
