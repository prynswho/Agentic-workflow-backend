from diagrams import Diagram, Node

with Diagram("LLM Architecture", show=False) as diag:
    llm = Node("LLM", color="green", style="filled")