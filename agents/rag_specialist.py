# agents/rag_specialist.py
import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_chroma import Chroma
from langchain_core.documents import Document
from state import AgentState

# Initialize local Ollama models
embeddings = OllamaEmbeddings(model="nomic-embed-text")
llm = ChatOllama(model="qwen2.5:7b", temperature=0)

PERSIST_DIR = "./chroma_db"
KB_DIR = "./knowledge_base"
DISTANCE_THRESHOLD = 1.2  # Lower score = closer match in Chroma L2 distance


def get_vectorstore() -> Chroma:
    """Loads existing ChromaDB or builds it from knowledge_base/*.txt if not found."""
    if os.path.exists(PERSIST_DIR) and os.listdir(PERSIST_DIR):
        return Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)

    docs = []
    kb_files = ["syntax_errors.txt", "runtime_errors.txt", "debugging_guide.txt"]

    for filename in kb_files:
        filepath = os.path.join(KB_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                # Split by '---' delimiter so each error entry is a clean chunk
                chunks = [c.strip() for c in content.split("---") if c.strip()]
                for chunk in chunks:
                    docs.append(Document(page_content=chunk, metadata={"source": filename}))

    if not docs:
        # Fallback empty document if txt files are currently blank
        docs = [Document(page_content="Placeholder debugging entry", metadata={"source": "init"})]

    return Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=PERSIST_DIR
    )


def rag_specialist_node(state: AgentState) -> AgentState:
    """
    Worker node for Member 2: Searches Knowledge Base and rewrites queries on NOT_FOUND.
    """
    # 1. Read input from Member 1's diagnosis payload
    diagnosis = state.get("diagnosis") or {}
    error_type = diagnosis.get("error_type", "UnknownError")
    error_message = diagnosis.get("error_message", "")
    source_line = diagnosis.get("source_line", "")  # Present on syntax errors

    attempt = state.get("search_attempt", 0)
    trace = list(state.get("react_trace", []))

    vectorstore = get_vectorstore()

    # 2. Formulate initial query (attempt 0) or rewrite query (attempt > 0)
    if attempt == 0:
        query = f"Python {error_type}: {error_message} {source_line}".strip()
        rewritten = ""
        thought_msg = f"Initial KB search for {error_type}: '{query}'"
    else:
        prev_query = state.get("rewritten_query") or f"Python {error_type}: {error_message}"
        rewrite_prompt = (
            f"You are a Python debugging search assistant. The previous search query '{prev_query}' "
            f"returned NOT_FOUND in our debugging knowledge base.\n"
            f"Error Type: {error_type}\n"
            f"Error Message: {error_message}\n"
            f"Rewrite this into a broader semantic search query focusing on how to fix {error_type} "
            f"in Python. Output ONLY the search query string, nothing else."
        )
        rewritten = llm.invoke(rewrite_prompt).content.strip().strip('"')
        query = rewritten
        thought_msg = f"Previous search returned NOT_FOUND. Rewrote query to: '{rewritten}'"

    # 3. Query ChromaDB with similarity score
    results = vectorstore.similarity_search_with_score(query, k=2)

    # 4. Evaluate threshold for FOUND vs NOT_FOUND
    if not results or results[0][1] > DISTANCE_THRESHOLD:
        knowledge_result = "NOT_FOUND"
        obs_msg = f"Search returned NOT_FOUND (best distance score > {DISTANCE_THRESHOLD})."
    else:
        knowledge_result = "\n\n".join(
            [f"[{doc.metadata.get('source')}]\n{doc.page_content}" for doc, score in results]
        )
        obs_msg = f"Found {len(results)} relevant solution(s). Best distance score: {results[0][1]:.3f}."

    # 5. Append ReAct trace entry
    trace.append({
        "agent": "rag_specialist",
        "attempt": attempt + 1,
        "thought": thought_msg,
        "action": f"ChromaDB similarity_search_with_score(query='{query}', k=2)",
        "observation": obs_msg
    })

    # 6. Return updated state fields
    return {
        "knowledge_result": knowledge_result,
        "rewritten_query": rewritten,
        "search_attempt": attempt + 1,
        "react_trace": trace
    }