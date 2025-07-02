import os
import streamlit as st
from dotenv import load_dotenv
from ingestion.pdf_loader import process_pdfs
from graph_loader import process_graph_docs, create_fulltext_index
from rag_module import get_rag_response
from datetime import datetime, timedelta
import pickle

load_dotenv()

st.set_page_config(page_title="Smart Banking Assistant", page_icon="\U0001F3E6")
st.title("\U0001F916 Smart Banking Assistant")

CHAT_HISTORY_FILE = "chat_history.pkl"

# Load chat history if exists
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "rb") as f:
            return pickle.load(f)
    return []

# Save chat history
def save_chat_history(history):
    with open(CHAT_HISTORY_FILE, "wb") as f:
        pickle.dump(history, f)

# Filter chat history to last 30 days
def filter_recent_chats(history):
    cutoff = datetime.now() - timedelta(days=30)
    return [chat for chat in history if chat["timestamp"] > cutoff]

chat_history = load_chat_history()
chat_history = filter_recent_chats(chat_history)
save_chat_history(chat_history)

# Track processed files
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# Sidebar: Upload PDFs
st.sidebar.title("\U0001F4C1 Upload Banking PDFs")
uploaded_files = st.sidebar.file_uploader("Upload PDF Files", type="pdf", accept_multiple_files=True)
if uploaded_files:
    new_files = []
    for file in uploaded_files:
        if file.name not in st.session_state.processed_files:
            with open(file.name, "wb") as f:
                f.write(file.read())
                new_files.append(file.name)
            st.session_state.processed_files.add(file.name)
    if new_files:
        process_pdfs(new_files)
        st.sidebar.success("PDFs processed and ingested!")

# Sidebar: LLM Model Selection
st.sidebar.title("\U0001F916 LLM Model Selection")
model_name = st.sidebar.selectbox("Select LLM Model", ["gpt-4", "gpt-4o", "gpt-3.5", "llama3", "mistral", "deepseek"])

# Sidebar: Chat Topics
st.sidebar.title("\U0001F4AC Chat History")
topic_mapping = {}
for idx, chat in enumerate(reversed(chat_history)):
    button_label = chat["question"][:30] + ("..." if len(chat["question"]) > 30 else "")
    if st.sidebar.button(button_label, key=f"topic_{idx}"):
        st.session_state.selected_topic = chat

# Main Area: Ask Question at Top
st.header("\U0001F4AC Ask Your Banking Question")
query = st.text_input("\U0001F9D1 Type your question:", key="question_input")

if st.button("Submit") and query:
    response, contexts, source_pdf = get_rag_response(query, model_name)
    st.session_state["last_response"] = response
    st.session_state["last_source_pdf"] = source_pdf
    st.session_state["last_question"] = query
    st.session_state.pop("selected_topic", None)

    chat_history.append({"question": query, "answer": response, "timestamp": datetime.now()})
    save_chat_history(chat_history)

# Show selected chat from topics if any
if "selected_topic" in st.session_state:
    selected = st.session_state.selected_topic
    st.subheader(selected["question"].capitalize())
    #st.markdown(f"👤**Q:** {selected['question']}")
    st.markdown(f"🤖**A:** {selected['answer']}")

# Show answer from latest submit if available and no topic selected
elif "last_response" in st.session_state:
    st.subheader(st.session_state["last_question"].capitalize())
   # st.markdown(f"👤**Q:** {st.session_state['last_question']}")
    st.markdown(f"🤖**A:** {st.session_state['last_response']}")

    if st.session_state["last_source_pdf"]:
        st.info(f"\U0001F4C4 **Source PDF:** {st.session_state['last_source_pdf']}")

    st.write("**Was this answer helpful?**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("\U0001F44D Yes", key="yes_btn"):
            st.success("Thank you for your feedback!")
    with col2:
        if st.button("\U0001F44E No", key="no_btn"):
            st.info("Thank you for your feedback!")

st.caption("© 2025 Smart Banking Assistant")
