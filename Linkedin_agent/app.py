import streamlit as st
import uuid
from typing import Dict, Any, Optional
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from Agent.agent import create_agent_graph

st.set_page_config(
    page_title="AI-Driven LinkedIn Content Automation Tool",
    page_icon="🤖",
    layout="wide"
)

def initialize_session_state():
    """Initialize session state variables"""
    if 'workflow' not in st.session_state:
        st.session_state.workflow = create_agent_graph()
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())
    if 'workflow_active' not in st.session_state:
        st.session_state.workflow_active = False
    if 'current_response' not in st.session_state:
        st.session_state.current_response = ""
    if 'feedback_message' not in st.session_state:
        st.session_state.feedback_message = ""
    if 'waiting_for_feedback' not in st.session_state:
        st.session_state.waiting_for_feedback = False
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'workflow_complete' not in st.session_state:
        st.session_state.workflow_complete = False

def start_workflow(user_input: str):
    """Start the AI agent workflow"""
    try:
        config = {'configurable': {'thread_id': st.session_state.thread_id}}
        
        st.session_state.conversation_history.append({
            'type': 'user',
            'content': user_input,
            'timestamp': st.session_state.get('timestamp', 0)
        })
        
        st.session_state.workflow_active = True
        st.session_state.workflow_complete = False
        
        result = st.session_state.workflow.invoke(
            {'messages': [HumanMessage(content=user_input)]},
            config
        )
        
        check_for_interrupts()
        
    except Exception as e:
        st.error(f"Error starting workflow: {str(e)}")
        st.session_state.workflow_active = False

def check_for_interrupts():
    """Check for workflow interrupts and handle them"""
    try:
        config = {'configurable': {'thread_id': st.session_state.thread_id}}
        current_state = st.session_state.workflow.get_state(config)
        
        if current_state.next == ():
            st.session_state.workflow_complete = True
            st.session_state.workflow_active = False
            st.session_state.waiting_for_feedback = False
            return
        
        if current_state.tasks:
            for task in current_state.tasks:
                if task.interrupts:
                    interrupt_data = task.interrupts[0]
                    st.session_state.current_response = interrupt_data.value.get('current_response', '')
                    st.session_state.feedback_message = interrupt_data.value.get('message', '')
                    st.session_state.waiting_for_feedback = True
                    return
                    
    except Exception as e:
        st.error(f"Error checking interrupts: {str(e)}")
        st.session_state.workflow_active = False

def provide_feedback(feedback: str):
    """Provide feedback to the AI agent"""
    try:
        config = {'configurable': {'thread_id': st.session_state.thread_id}}
        
        st.session_state.conversation_history.append({
            'type': 'feedback',
            'content': feedback,
            'response': st.session_state.current_response
        })
        
        if feedback.lower() in ['approve', 'yes', 'ok', 'good', 'accept']:
            st.session_state.workflow.invoke(Command(resume=feedback), config)
            st.session_state.workflow_complete = True
            st.session_state.workflow_active = False
            st.session_state.waiting_for_feedback = False
            
            st.session_state.conversation_history.append({
                'type': 'ai_final',
                'content': st.session_state.current_response
            })
            
        else:
            st.session_state.workflow.invoke(Command(resume=feedback), config)
            st.session_state.waiting_for_feedback = False
            
            check_for_interrupts()
            
    except Exception as e:
        st.error(f"Error providing feedback: {str(e)}")
        st.session_state.workflow_active = False

def reset_workflow():
    """Reset the workflow and start fresh"""
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.workflow_active = False
    st.session_state.current_response = ""
    st.session_state.feedback_message = ""
    st.session_state.waiting_for_feedback = False
    st.session_state.conversation_history = []
    st.session_state.workflow_complete = False

initialize_session_state()

st.title("🤖 AI-Driven LinkedIn Content Automation Tool")
st.markdown("---")

with st.sidebar:
    st.header("🔧 Controls")
    
    if st.button("🔄 Reset Workflow", type="secondary"):
        reset_workflow()
        st.rerun()
    
    st.markdown("---")
    st.subheader("📊 Status")
    
    if st.session_state.workflow_active:
        st.success("🟢 Workflow Active")
    elif st.session_state.workflow_complete:
        st.info("✅ Workflow Complete")
    else:
        st.warning("⭕ Workflow Inactive")
    
    if st.session_state.waiting_for_feedback:
        st.warning("⏳ Waiting for Feedback")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("💬 Conversation")
    
    if st.session_state.conversation_history:
        for i, item in enumerate(st.session_state.conversation_history):
            if item['type'] == 'user':
                with st.chat_message("user"):
                    st.write(item['content'])
            elif item['type'] == 'ai_final':
                with st.chat_message("assistant"):
                    st.write(item['content'])
            elif item['type'] == 'feedback':
                with st.chat_message("user"):
                    st.write(f"**Feedback:** {item['content']}")
    
    if not st.session_state.workflow_active and not st.session_state.waiting_for_feedback:
        st.subheader(" Start New Task")
        user_input = st.text_area(
            "What would you like the AI agent to do?",
            placeholder="e.g., generate a LinkedIn post about recent AI trends",
            height=100,
            key="user_input"
        )
        
        if st.button("Start Workflow", type="primary", disabled=not user_input.strip()):
            if user_input.strip():
                start_workflow(user_input.strip())
                st.rerun()

with col2:
    st.subheader(" AI Response & Feedback")
    
    if st.session_state.waiting_for_feedback:
        st.markdown("### AI Response:")
        st.info(st.session_state.current_response)
        
        st.markdown("### Feedback Request:")
        st.warning(st.session_state.feedback_message)
        
        st.markdown("### Your Feedback:")
        feedback_input = st.text_area(
            "Provide your feedback:",
            placeholder="Enter your feedback or type 'approve' to accept the response",
            height=100,
            key="feedback_input"
        )
        
        col_approve, col_feedback = st.columns(2)
        
        with col_approve:
            if st.button(" Approve", type="primary"):
                provide_feedback("approve")
                st.rerun()
        
        with col_feedback:
            if st.button("Send Feedback", disabled=not feedback_input.strip()):
                if feedback_input.strip():
                    provide_feedback(feedback_input.strip())
                    st.rerun()
    
    elif st.session_state.workflow_complete:
        st.success("Workflow completed successfully!")
        if st.session_state.conversation_history:
            final_response = next((item for item in reversed(st.session_state.conversation_history) 
                                 if item['type'] == 'ai_final'), None)
            if final_response:
                st.markdown("###  Final Result:")
                st.success(final_response['content'])
    
    elif st.session_state.workflow_active:
        st.info(" Processing your request...")
        
        if st.button(" Check Status"):
            check_for_interrupts()
            st.rerun()
    
    else:
        st.markdown("###  How it works:")
        st.markdown("""
        1. **Enter your request** in the text area
        2. **Start the workflow** by clicking the button
        3. **Review the AI response** when prompted
        4. **Provide feedback** or approve the response if it is satisfactory
        5. **Iterate** until you're satisfied with the result
        """)


st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
         AI-Driven LinkedIn Content Automation Tool with Human Feedback Loop • Built with Streamlit & LangGraph
    </div>
    """,
    unsafe_allow_html=True
)

if st.session_state.workflow_active and not st.session_state.waiting_for_feedback:
    import time
    time.sleep(1)
    st.rerun()