from langchain_postgres import PostgresChatMessageHistory
from ..config import settings
from psycopg import AsyncConnection

# Create connection and table once
_connection = None
_table_created = False

async def _get_connection():
    """Get or create a database connection, reconnecting if closed."""
    global _connection

    if _connection is None:
        _connection = await AsyncConnection.connect(settings.database_url)
    else:
        # Check if connection is closed and reconnect if needed
        try:
            await _connection.execute("SELECT 1")
        except Exception:
            _connection = await AsyncConnection.connect(settings.database_url)

    return _connection

async def initialize_chat_table():
    """Initialize the chat messages table on startup. Called once when FastAPI starts."""
    global _table_created

    if _table_created:
        return

    conn = await _get_connection()

    # Use langchain_postgres built-in table creation
    from langchain_postgres import PostgresChatMessageHistory
    await PostgresChatMessageHistory.acreate_tables(conn, "gorgia_chat_messages")

    # Add browser_id column if it doesn't exist (custom field for our use case)
    async with conn.cursor() as cur:
        await cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='gorgia_chat_messages' AND column_name='browser_id'
                ) THEN
                    ALTER TABLE gorgia_chat_messages ADD COLUMN browser_id TEXT;
                    CREATE INDEX idx_browser_id ON gorgia_chat_messages(browser_id);
                END IF;
            END $$;
        """)
    await conn.commit()
    _table_created = True
    print("✅ Chat table initialized successfully")

async def get_message_history(session_id: str, browser_id: str = None) -> PostgresChatMessageHistory:
    global _connection, _table_created

    _connection = await _get_connection()


    # Store browser_id in the session if provided (after messages are added)
    if browser_id:
        async with _connection.cursor() as cur:
            await cur.execute("""
                UPDATE gorgia_chat_messages
                SET browser_id = %s
                WHERE session_id = %s
            """, (browser_id, session_id))
        await _connection.commit()

    return PostgresChatMessageHistory(
        "gorgia_chat_messages",
        session_id,
        async_connection=_connection
    )