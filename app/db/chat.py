from langchain_postgres import PostgresChatMessageHistory
from ..config import settings
import psycopg

# Create connection and table once
_connection = None
_table_created = False

def get_message_history(session_id: str, browser_id: str = None) -> PostgresChatMessageHistory:
    global _connection, _table_created

    if _connection is None:
        _connection = psycopg.connect(settings.database_url)

    # Store browser_id in the session if provided (after messages are added)
    if browser_id:
        with _connection.cursor() as cur:
            cur.execute("""
                UPDATE gorgia_chat_messages
                SET browser_id = %s
                WHERE session_id = %s
            """, (browser_id, session_id))
        _connection.commit()

    return PostgresChatMessageHistory(
        "gorgia_chat_messages",
        session_id,
        sync_connection=_connection
    )