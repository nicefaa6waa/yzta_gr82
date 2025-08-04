from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class ChatDB:
    def __init__(self, db_path=None):
        if db_path is None:
            # FIXED: Use persistent database path that survives restarts
            self.db_path = self._get_persistent_db_path()
        else:
            self.db_path = db_path
        self.init_db()
        self.user_keys = {}  # Store user encryption keys in memory

    def _get_persistent_db_path(self):
        """Get persistent database path that survives server restarts"""
        # Try multiple persistent locations in order of preference
        possible_paths = [
            "/opt/render/project/src/data",  # Render persistent storage
            "/tmp/data",                     # Fallback for development
            "./data",                       # Local fallback
        ]
        
        # Create the first available directory
        for path in possible_paths:
            try:
                data_dir = Path(path)
                data_dir.mkdir(parents=True, exist_ok=True)
                
                # Test if we can write to this directory
                test_file = data_dir / "test_write.tmp"
                test_file.write_text("test")
                test_file.unlink()
                
                db_path = data_dir / "radiglow_chats.db"
                print(f"✅ Using persistent chat database path: {db_path.absolute()}")
                return str(db_path)
                
            except Exception as e:
                print(f"❌ Cannot use chat path {path}: {e}")
                continue
        
        # Ultimate fallback - current directory
        db_path = Path("radiglow_chats.db")
        print(f"⚠️  Using fallback chat database path: {db_path.absolute()}")
        return str(db_path)

    def get_connection(self):
        """Get database connection with proper settings"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        
        # Enable WAL mode for better concurrency and crash recovery
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=1000")
        conn.execute("PRAGMA temp_store=memory")
        
        return conn

    def init_db(self):
        """Initialize chat database with proper error handling"""
        try:
            conn = self.get_connection()
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
            
            # Create indexes for better performance
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id 
                ON chat_sessions(user_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id 
                ON chat_messages(chat_id)
            ''')
            
            c.execute('''
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at 
                ON chat_sessions(updated_at DESC)
            ''')
            
            conn.commit()
            
            # Check existing data to confirm persistence
            c.execute("SELECT COUNT(*) as count FROM chat_sessions")
            chat_count = c.fetchone()['count']
            
            c.execute("SELECT COUNT(*) as count FROM chat_messages")
            message_count = c.fetchone()['count']
            
            print(f"✅ Chat database initialized successfully")
            print(f"📊 Existing chats: {chat_count}")
            print(f"📊 Existing messages: {message_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Chat database initialization error: {e}")
            raise
    
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
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            chat_id = base64.urlsafe_b64encode(os.urandom(16)).decode()
            now = datetime.utcnow().isoformat()
            
            c.execute('''
            INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (chat_id, user_id, title, now, now))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Chat created: {chat_id} for user {user_id}")
            return chat_id
            
        except Exception as e:
            print(f"❌ Chat creation error: {e}")
            raise
    
    def add_message(self, chat_id: str, content: str, sender: str, user_id: str, user_key: bytes) -> str:
        try:
            conn = self.get_connection()
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
            
            print(f"✅ Message added to chat {chat_id}")
            return message_id
            
        except Exception as e:
            print(f"❌ Add message error: {e}")
            raise
    
    def get_chat_history(self, chat_id: str, user_key: bytes) -> list:
        try:
            conn = self.get_connection()
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
            
        except Exception as e:
            print(f"❌ Get chat history error: {e}")
            return []

    def get_user_chats(self, user_id: str) -> list:
        try:
            conn = self.get_connection()
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
            
        except Exception as e:
            print(f"❌ Get user chats error: {e}")
            return []
    
    def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat and all its messages"""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # First check if the chat belongs to the user
            c.execute('SELECT user_id FROM chat_sessions WHERE id = ?', (chat_id,))
            result = c.fetchone()
            
            if not result or result[0] != user_id:
                print(f"❌ Delete chat failed: Chat {chat_id} not found or not owned by user {user_id}")
                return False
            
            # Delete messages first (due to foreign key)
            c.execute('DELETE FROM chat_messages WHERE chat_id = ?', (chat_id,))
            messages_deleted = c.rowcount
            
            # Delete the chat session
            c.execute('DELETE FROM chat_sessions WHERE id = ?', (chat_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Chat deleted: {chat_id} ({messages_deleted} messages)")
            return True
            
        except Exception as e:
            print(f"❌ Delete chat error: {e}")
            return False