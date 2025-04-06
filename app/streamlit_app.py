import os
import sys
import traceback
import streamlit as st
from dotenv import load_dotenv

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import load_courses
from core.intent_parser import parse_intent
from core.course_filter import filter_courses
from core.response_generator import generate_response
from core.memory import update_memory, get_conversation_history
from utils.formatter import format_course_list

# Load environment variables
load_dotenv()

# Initialize session state for API key
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")

# Set page config
st.set_page_config(
    page_title="University Course Assistant",
    page_icon="🎓",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "error" not in st.session_state:
    st.session_state["error"] = None
if "is_processing" not in st.session_state:
    st.session_state["is_processing"] = False

# App title
st.title("🎓 University Course Assistant")

# API Key input in sidebar
with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("OpenAI API Key", value=st.session_state["openai_api_key"], type="password")
    if api_key:
        st.session_state["openai_api_key"] = api_key
    else:
        st.warning("Please enter your OpenAI API key to continue.")
        st.stop()

    st.header("About")
    st.markdown("""
    This assistant helps you find and understand university courses in the UK.
    
    You can ask questions like:
    - What computer science courses are available?
    - Show me business courses at LSE
    - What are the entry requirements for Oxford's Computer Science program?
    - Compare the fees between different universities
    """)

# Load course data
@st.cache_data
def load_data():
    try:
        return load_courses()
    except Exception as e:
        st.error(f"Error loading course data: {str(e)}")
        st.error("Please check that the courses.json file exists and is properly formatted.")
        return None

df = load_data()

st.markdown("Ask me anything about UK university courses!")

# Display course data info
if df is not None:
    st.sidebar.header("Course Data")
    st.sidebar.write(f"Loaded {len(df)} courses from {len(df['university'].unique())} universities")
    
    # Display a sample of courses
    if st.sidebar.checkbox("Show sample courses"):
        st.sidebar.dataframe(df[["name", "university", "study_mode", "duration"]].head(5))
else:
    st.sidebar.error("Course data is not available")

# Display chat messages
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Display error if any
if st.session_state["error"]:
    st.error(st.session_state["error"])
    st.session_state["error"] = None

# Chat input
if prompt := st.chat_input("What would you like to know about university courses?"):
    # Add user message to chat history
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Set processing state to True
    st.session_state["is_processing"] = True
    
    # Display thinking spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Check if data is loaded
            if df is None:
                st.error("Course data is not available. Please check the data file.")
                st.session_state["messages"].append({"role": "assistant", "content": "I'm sorry, I can't help you right now because the course data is not available. Please try again later."})
                st.markdown("I'm sorry, I can't help you right now because the course data is not available. Please try again later.")
                st.session_state["is_processing"] = False
                st.stop()
            
            # Get conversation history
            history = get_conversation_history()
            
            # Parse user intent
            try:
                parsed = parse_intent(prompt, history, api_key=st.session_state["openai_api_key"])
            except Exception as e:
                st.session_state["error"] = f"Error parsing intent: {str(e)}"
                parsed = {
                    "intent": "search",
                    "entities": {},
                    "user_preferences": {},
                    "comparison_details": {},
                    "clarification_needed": None
                }
            
            # Filter courses based on intent
            try:
                matched = filter_courses(parsed, df)
            except Exception as e:
                st.session_state["error"] = f"Error filtering courses: {str(e)}"
                matched = df.iloc[0:0]  # Empty DataFrame
            
            # Generate response
            try:
                reply = generate_response(prompt, parsed, matched, history, api_key=st.session_state["openai_api_key"])
            except Exception as e:
                st.session_state["error"] = f"Error generating response: {str(e)}"
                reply = "I'm sorry, I encountered an error while processing your request. Please try again."
            
            # Update memory
            try:
                update_memory(parsed, reply, prompt, matched["id"].tolist() if not matched.empty else [])
            except Exception as e:
                st.session_state["error"] = f"Error updating memory: {str(e)}"
                # Continue without updating memory
            
            # Add assistant response to chat history
            st.session_state["messages"].append({"role": "assistant", "content": reply})
            
            # Display assistant response
            st.markdown(reply)
    
    # Set processing state to False
    st.session_state["is_processing"] = False 