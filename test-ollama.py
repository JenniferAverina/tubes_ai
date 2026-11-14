
from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:7b",
    temperature=0
)

response = llm.invoke(
    "Explain what a Python SyntaxError is in two sentences."
)

print(response.content)
