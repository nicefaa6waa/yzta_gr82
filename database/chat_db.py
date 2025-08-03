from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import sqlite3
import json
from datetime import datetime

class ChatDB:
    def __init__(self, db_path=None):
        if db_path is None:
            # Store in the same directory as the main database
            self.db_path = os.path.join(os.path.dirname(__file__), '..', 'chat.db')
        else:
            self.db_path = db_path
        self.init_db()
        self.user_keys = {}  # Store user encryption keys in memory

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create tables
        c.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )''')
        
        c.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            encrypted_content TEXT NOT NULL,
            sender TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (chat_id) REFERENCES chat_sessions(id)
        )''')
        
        conn.commit()
        conn.close()
    
    def generate_user_key(self, user_id: str, password: str) -> bytes:
        """Generate a unique encryption key for each user"""
        salt = user_id.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def get_user_key(self, user_id: str, password: str) -> bytes:
        """Get or create user's encryption key"""
        if user_id not in self.user_keys:
            self.user_keys[user_id] = self.generate_user_key(user_id, password)
        return self.user_keys[user_id]

    def encrypt_message(self, message: str, user_key: bytes) -> str:
        """Encrypt a message using user's key"""
        f = Fernet(user_key)
        return f.encrypt(message.encode()).decode()

    def decrypt_message(self, encrypted_message: str, user_key: bytes) -> str:
        """Decrypt a message using user's key"""
        try:
            f = Fernet(user_key)
            return f.decrypt(encrypted_message.encode()).decode()
        except:
            return "***Message Encrypted***"

    def create_chat(self, user_id: str, title: str) -> str:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        chat_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
        now = datetime.utcnow().isoformat()
        
        c.execute('''
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, user_id, title, now, now))
        
        conn.commit()
        conn.close()
        return chat_id
    
    def add_message(self, chat_id: str, content: str, sender: str, user_id: str, user_key: bytes) -> str:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        message_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
        encrypted_content = self.encrypt_message(content, user_key)
        now = datetime.utcnow().isoformat()
        
        c.execute('''
        INSERT INTO chat_messages (id, chat_id, encrypted_content, sender, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (message_id, chat_id, encrypted_content, sender, now))
        
        c.execute('UPDATE chat_sessions SET updated_at = ? WHERE id = ?', (now, chat_id))
        
        conn.commit()
        conn.close()
        return message_id
    
    def get_chat_history(self, chat_id: str, user_key: bytes) -> list:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT encrypted_content, sender, created_at 
        FROM chat_messages 
        WHERE chat_id = ? 
        ORDER BY created_at
        ''', (chat_id,))
        
        messages = []
        for row in c.fetchall():
            messages.append({
                'content': self.decrypt_message(row[0], user_key),
                'sender': row[1],
                'created_at': row[2]
            })
        
        conn.close()
        return messages

    def get_user_chats(self, user_id: str) -> list:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''
        SELECT id, title, created_at, updated_at 
        FROM chat_sessions 
        WHERE user_id = ? 
        ORDER BY updated_at DESC
        ''', (user_id,))
        
        chats = []
        for row in c.fetchall():
            chats.append({
                'id': row[0],
                'title': row[1],
                'created_at': row[2],
                'updated_at': row[3]
            })
        
        conn.close()
        return chats
    
    def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat and all its messages"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        try:
            # First check if the chat belongs to the user
            c.execute('SELECT user_id FROM chat_sessions WHERE id = ?', (chat_id,))
            result = c.fetchone()
            
            if not result or result[0] != user_id:
                return False
            
            # Delete messages first (due to foreign key)
            c.execute('DELETE FROM chat_messages WHERE chat_id = ?', (chat_id,))
            
            # Delete the chat session
            c.execute('DELETE FROM chat_sessions WHERE id = ?', (chat_id,))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting chat: {e}")
            return False
        finally:
            conn.close()