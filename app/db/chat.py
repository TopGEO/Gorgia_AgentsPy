from langchain_postgres import PostgresChatMessageHistory
from ..config import settings
import psycopg

# Create connection and table once
_connection = None
_table_created = False

def _get_connection():
    """Get or create a database connection, reconnecting if closed."""
    global _connection

    if _connection is None:
        _connection = psycopg.connect(settings.database_url)
    else:
        # Check if connection is closed and reconnect if needed
        try:
            _connection.execute("SELECT 1")
        except (psycopg.OperationalError, psycopg.InterfaceError):
            _connection = psycopg.connect(settings.database_url)

    return _connection

def get_message_history(session_id: str, browser_id: str = None) -> PostgresChatMessageHistory:
    global _connection, _table_created

    _connection = _get_connection()


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