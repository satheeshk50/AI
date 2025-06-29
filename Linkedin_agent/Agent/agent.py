from langgraph.graph import StateGraph, START, END
from .nodes import State, chatbot, tools_node, human_feedback_node, post_to_linkedin , should_continue, should_continue_after_tools, should_continue_after_feedback,memory

def create_agent_graph() -> StateGraph:
    graph = StateGraph(State)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tools", tools_node)
    graph.add_node("human_feedback", human_feedback_node)
    graph.add_node("post", post_to_linkedin)
    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges(
        "chatbot",
        should_continue,
        {
            "tools": "tools",
            "human_feedback": "human_feedback",
        }
    )
    graph.add_conditional_edges(
        "tools",
        should_continue_after_tools,
        {
            "chatbot": "chatbot"
        }
    )
    graph.add_conditional_edges(
        "human_feedback", 
        should_continue_after_feedback, 
        {
            "post": "post",
            "chatbot": "chatbot"
        }
    )
    graph.add_edge("post", END)
    workflow = graph.compile(checkpointer=memory)
    graph_image = workflow.get_graph().draw_mermaid_png()
        
    with open('agent_graph.png', "wb") as f:
        f.write(graph_image)
    return workflow