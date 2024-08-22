from ..utils.database import get_db_connection

def create_chat_history_table():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id BIGINT AUTO_RANDOM PRIMARY KEY,
                session_id VARCHAR(255),
                user_input TEXT,
                bot_response TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """)
        connection.commit()
        print("chat_history table created successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        connection.close()

def store_chat_message(session_id, user_input, bot_response):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            insert_sql = """
            INSERT INTO chat_history 
            (session_id, user_input, bot_response) 
            VALUES (%s, %s, %s)
            """
            cursor.execute(insert_sql, (session_id, user_input, bot_response))
        connection.commit()
        print(f"Chat message stored successfully for session {session_id}")
    except Exception as e:
        print(f"An error occurred while storing the chat message: {e}")
        connection.rollback()
    finally:
        connection.close()

def get_chat_history(session_id, limit=5):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            select_sql = """
            SELECT user_input, bot_response 
            FROM chat_history 
            WHERE session_id = %s 
            ORDER BY timestamp DESC 
            LIMIT %s
            """
            cursor.execute(select_sql, (session_id, limit))
            results = cursor.fetchall()
        return results
    except Exception as e:
        print(f"An error occurred while retrieving chat history: {e}")
        return []
    finally:
        connection.close()
