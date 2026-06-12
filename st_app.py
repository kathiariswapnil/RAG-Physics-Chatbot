from Database_operations.db_operations import create_conversation, save_message, get_messages, get_all_conversations, update_conversation_title, delete_conversation
from workflow import app
from pathlib import Path
import streamlit as st


st.set_page_config(
    page_title="CBSE Physics RAG Tutor",
    layout="wide"
)

st.title("CBSE Physics RAG Tutor")

st.sidebar.title("Conversations")
if st.sidebar.button("Rerun"):
    st.rerun()
if st.sidebar.button("➕ New Chat"):
    new_id = create_conversation(title="New Physics Chat")
    st.session_state.conversation_id = (new_id)
    st.session_state.messages = []
    st.rerun()

conversations = get_all_conversations()

for convo in conversations:
    title = (convo.title or f"Chat {convo.id}")
    col1, col2 = (st.sidebar.columns([5, 1]))
    # =========================
    # LOAD CHAT BUTTON
    # =========================
    if col1.button(title,key=f"load_{convo.id}"):
        st.session_state.conversation_id = (convo.id)
        db_messages = get_messages(convo.id)
        st.session_state.messages = [
            {
                "role": msg.role,
                "content": msg.content
            }
            for msg in db_messages
        ]
        st.rerun()
    # ========================
    # DELETE BUTTON
    # ========================
    if col2.button("🗑",key=f"delete_{convo.id}"):
        delete_conversation(convo.id)
        # clear current chat
        if (st.session_state.conversation_id == convo.id):
            st.session_state.messages = []
            st.session_state.conversation_id = create_conversation()
        st.rerun()

if "conversation_id" not in st.session_state:
    convo_id = create_conversation(title="Physics Chat")
    st.session_state.conversation_id = convo_id
    st.session_state.messages = []

st.write("Ask Physics questions")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        for diagram_path in message.get("generated_diagrams", []):
            if Path(diagram_path).exists():
                st.image(diagram_path, caption="Generated diagram", use_container_width=True)
        for video_path in message.get("generated_videos", []):
            if Path(video_path).exists():
                st.video(video_path)

user_query = st.chat_input("Ask a Physics question...")

if user_query:
    cleaned_query = user_query.lower().strip()
    if cleaned_query in ["exit", "quit", "bye"]:
        st.warning("Chat session ended.")
        st.info("Session ended.")
        
    if len(st.session_state.messages) == 0:
        title = user_query.strip().replace("\n", " ")[:50]
        update_conversation_title(st.session_state.conversation_id, title)
    
    save_message(st.session_state.conversation_id, "user", user_query)
    st.session_state.messages.append({
    "role": "user",
    "content": user_query
})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving physics concepts..."):
            result = app.invoke({"question": user_query})
            ai_message = result["final_answer"]
            generated_diagrams = result.get("generated_diagrams", [])
            generated_videos = result.get("generated_videos", [])
            if not ai_message:
                ai_message = "No relevant information found in the knowledge base."
        st.markdown(ai_message)
        for diagram_path in generated_diagrams:
            if Path(diagram_path).exists():
                st.image(diagram_path, caption="Generated diagram", use_container_width=True)
            else:
                st.warning(f"Diagram file was not found: {diagram_path}")
        for video_path in generated_videos:
            if Path(video_path).exists():
                st.video(video_path)
            else:
                st.warning(f"Video file was not found: {video_path}")
        with st.expander("Execution Trace"):
            for step in result["execution_trace"]:
                st.write(step)
        
    save_message(st.session_state.conversation_id, "assistant", ai_message)
    st.session_state.messages.append({
    "role": "assistant",
    "content": ai_message,
    "generated_diagrams": generated_diagrams,
    "generated_videos": generated_videos
})
