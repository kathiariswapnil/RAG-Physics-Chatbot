from models import Conversation,Message
from db import SessionLocal
from models import Message

# =========================================
# CREATE CONVERSATION
# =========================================

def create_conversation(title="New Physics Chat"):
    db = SessionLocal()
    conversation = Conversation(title=title)

    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    db.close()
    
    return conversation.id

def save_message(conversation_id, role, content):
    db = SessionLocal()
    message = Message(conversation_id=conversation_id, role=role, content=content)

    db.add(message)
    db.commit()
    db.close()
    
def get_messages(conversation_id):
    db = SessionLocal()
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all())
    
    db.close()
    
    return messages

def get_all_conversations():
    db = SessionLocal()
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    db.close()

    return conversations

def get_messages(conversation_id):
    db = SessionLocal()
    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id
            == conversation_id
        )
        .order_by(Message.created_at)
        .all()
    )
    db.close()

    return messages

def update_conversation_title(conversation_id, title):
    db = SessionLocal()
    convo = (
        db.query(Conversation)
        .filter(Conversation.id== conversation_id)
        .first()
    )
    if convo:
        convo.title = title
        db.commit()

    db.close()
    
def delete_conversation(conversation_id):
    db = SessionLocal()

    # delete messages first

    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    
    # delete conversation

    db.query(Conversation).filter(Conversation.id == conversation_id).delete()

    db.commit()
    db.close()