import sqlite3
import json

class ChatDatabase:
    def __init__(self, db_name='chat_database.db'):
        self.db_name = db_name
        self._connect_to_database()

    def _connect_to_database(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            self._check_table_exists()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def _check_table_exists(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat'")
        if self.cursor.fetchone() is None:
            self._create_table()

    def _create_table(self):
        """Creates the chat table if it doesn't exist."""
        self.cursor.execute('''
            CREATE TABLE chat (
                conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1  -- 1 for active, 0 for inactive
            )
        ''')
        self.conn.commit()

    def insert_conversation(self, conversation, active=True):
        """Inserts a new conversation into the chat table."""
        conversation_json = json.dumps(conversation)
        self.cursor.execute('''
            INSERT INTO chat (conversation, active)
            VALUES (?,?)
        ''', (conversation_json, int(active)))
        self.conn.commit()
        return self.cursor.lastrowid  # Return the ID of the inserted row
    
    def get_conversation(self, conversation_id):
        """Retrieves a conversation by ID."""
        self.cursor.execute('''
            SELECT conversation, active FROM chat
            WHERE conversation_id =?
        ''', (conversation_id,))
        result = self.cursor.fetchone()
        if result:
            conversation_json, active = result
            conversation = json.loads(conversation_json)
            return {"conversation": conversation, "active": bool(active)}
        else:
            return None

    def update_conversation(self, conversation_id, new_conversation):
        """Updates an existing conversation by ID."""
        conversation_json = json.dumps(new_conversation)
        self.cursor.execute('''
            UPDATE chat
            SET conversation =?
            WHERE conversation_id =?
        ''', (conversation_json, conversation_id))
        self.conn.commit()

    def delete_conversation(self, conversation_id):
        """Deletes a conversation by ID."""
        self.cursor.execute('''
            DELETE FROM chat
            WHERE conversation_id =?
        ''', (conversation_id,))
        self.conn.commit()

    def add_message_to_conversation(self, conversation_id, new_message):
        """Appends a new message to an existing conversation."""
        conversation_data = self.get_conversation(conversation_id)
        if conversation_data is None:
            raise ValueError(f"Conversation with ID {conversation_id} does not exist.")
        conversation = conversation_data["conversation"]
        conversation.append(new_message)
        self.update_conversation(conversation_id, conversation)

    def set_conversation_active_status(self, conversation_id, active):
        """Sets the active or inactive status of a conversation."""
        self.cursor.execute('''
            UPDATE chat
            SET active =?
            WHERE conversation_id =?
        ''', (int(active), conversation_id))
        self.conn.commit()

    def close_connection(self):
        self.conn.close()

# Example usage
if __name__ == "__main__":
    chat_db = ChatDatabase()

    initial_conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi! How can I help you today?"}
    ]

    chat_db.insert_conversation(initial_conversation, active=True)

    new_message = {"role": "user", "content": "What is the weather like today?"}
    chat_db.add_message_to_conversation(1, new_message)

    retrieved_conversation = chat_db.get_conversation(1)
    print("Retrieved Conversation:", retrieved_conversation)

    chat_db.set_conversation_active_status(1, active=False)
    
    updated_conversation = chat_db.get_conversation(1)
    print("Updated Conversation (Inactive):", updated_conversation)

    chat_db.delete_conversation(1)

    chat_db.close_connection()