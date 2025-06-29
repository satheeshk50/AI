from langchain_groq import ChatGroq
from typing import Annotated, Union
from typing_extensions import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph.message import add_messages
import os
from dotenv import load_dotenv
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt
from .prompts import system_prompt
from .tools import tools, tools_node
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.linkedin_api import linkedin_api
from IPython.display import display, Image


load_dotenv()

memory = MemorySaver()

os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY')
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ['LANGSMITH_PROJECT'] = 'LinkedIn Agent'
os.environ['TAVILY_API_KEY'] = os.getenv('TAVILY_API_KEY')

class State(TypedDict):
    messages: Annotated[list[Union[HumanMessage, AIMessage, SystemMessage, ToolMessage]], add_messages]
    feedback: str
    current_content: str
    approve: bool
    
llm = ChatGroq(model="llama-3.1-8b-instant")

llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State) -> State:
    feedback = state.get('feedback', '')
    current_content = state.get('current_content', '')
    if feedback and feedback.strip() and not state.get('approve', False):
        revision_prompt = f"""
        Original response: {current_content}
        
        Human feedback: {feedback}
        
        Please revise the response based on the feedback provided.
        """
        messages_with_revision = state['messages'] + [HumanMessage(content=revision_prompt)]
        response = llm_with_tools.invoke(messages_with_revision)
        return {
            'messages': [response],
            'current_content': response.content,
            'feedback': '',
            'approve': False
        }
    else:
        state['messages'].insert(0, SystemMessage(content=system_prompt))
        response = llm_with_tools.invoke(state['messages'])
        return {
            'messages': [response],
            'current_content': response.content,
            'feedback': '',
            'approve': False
        }

def human_feedback_node(state: State) -> State:
    current_content = state.get('current_content', 'No current response')
    feedback = interrupt({
        "current_response": current_content,
        "message": "Please provide feedback: Type 'approve'/'yes' to accept, or provide specific feedback for revision"
    })
    if feedback:
        feedback_text = feedback.strip().lower()
        if feedback_text in ['approve', 'yes', 'ok', 'good', 'accept']:
            return {
                'approve': True,
                'feedback': '',
                'messages': state['messages'],
                'current_content': state['current_content']
            }
        else:
            return {
                'approve': False,
                'feedback': feedback,
                'messages': state['messages'],
                'current_content': state['current_content']
            }
    return {
        'approve': False,
        'feedback': 'No feedback provided. Please revise.',
        'messages': state['messages'],
        'current_content': state['current_content']
    }

def post_to_linkedin(state: State) -> State:
    response = linkedin_api(state['current_content'])
    if 'error' in response:
        state['messages'].append(AIMessage(content=f"{response['error']}"))
    else:
        state['messages'].append(AIMessage(content=f"{response['content']}"))
    return state

def should_continue(state: State) -> str:
    last_message = state['messages'][-1] if state['messages'] else None
    if last_message and hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return "human_feedback"

def should_continue_after_feedback(state: State) -> str:
    if state.get('approve') == True:
        return 'post'
    else:
        return "chatbot"

def should_continue_after_tools(state: State) -> str:
    return "chatbot"