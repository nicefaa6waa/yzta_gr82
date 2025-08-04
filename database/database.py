import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict
import json
from passlib.context import CryptContext
import os
from pathlib import Path

class Database:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def __init__(self):
        # FIXED: Use persistent database path that survives restarts
        self.db_path = self._get_persistent_db_path()
        self.init_db()
    
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
                
                db_path = data_dir / "radiglow_users.db"
                print(f"✅ Using persistent database path: {db_path.absolute()}")
                return str(db_path)
                
            except Exception as e:
                print(f"❌ Cannot use path {path}: {e}")
                continue
        
        # Ultimate fallback - current directory
        db_path = Path("radiglow_users.db")
        print(f"⚠️  Using fallback database path: {db_path.absolute()}")
        return str(db_path)
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        
        # Enable WAL mode for better concurrency and crash recovery
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=1000")
        conn.execute("PRAGMA temp_store=memory")
        
        return conn
    
    def init_db(self):
        """Initialize database with proper error handling"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create only user and guest usage tables
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS guest_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL,
                    date TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(ip_address, date)
                );
                
                -- Create indexes for better performance
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                CREATE INDEX IF NOT EXISTS idx_guest_usage_ip_date ON guest_usage(ip_address, date);
            ''')
            
            conn.commit()
            
            # Check existing data to confirm persistence
            cursor.execute("SELECT COUNT(*) as count FROM users")
            user_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM guest_usage")
            usage_count = cursor.fetchone()['count']
            
            print(f"✅ Database initialized successfully")
            print(f"📊 Existing users: {user_count}")
            print(f"📊 Guest usage records: {usage_count}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, name: str, password: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Check if email already exists
            if self.get_user_by_email(email):
                conn.close()
                print(f"❌ User creation failed: Email {email} already exists")
                return None
            
            # Hash password before storing
            hashed_password = self.pwd_context.hash(password)
            
            cursor.execute(
                "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
                (email, name, hashed_password)
            )
            
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ User created successfully: {email} (ID: {user_id})")
            return self.get_user_by_email(email)
            
        except Exception as e:
            print(f"❌ User creation error: {e}")
            return None

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, email, name, password_hash FROM users WHERE email = ?",
                (email,)
            )
            
            user = cursor.fetchone()
            conn.close()
            
            if user and self.pwd_context.verify(password, user["password_hash"]):
                print(f"✅ Authentication successful: {email}")
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"]
                }
            else:
                print(f"❌ Authentication failed: {email}")
                return None
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, email, name, created_at FROM users WHERE email = ?",
                (email,)
            )
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "created_at": user["created_at"]
                }
            return None
            
        except Exception as e:
            print(f"❌ Get user error: {e}")
            return None
    
    def get_guest_usage(self, ip_address: str, date: str) -> int:
        """Get guest usage count for today"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT usage_count FROM guest_usage WHERE ip_address = ? AND date = ?",
                (ip_address, date)
            )
            
            result = cursor.fetchone()
            conn.close()
            
            return result["usage_count"] if result else 0
            
        except Exception as e:
            print(f"❌ Get guest usage error: {e}")
            return 0
    
    def increment_guest_usage(self, ip_address: str, date: str) -> int:
        """Increment guest usage count"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Try to update existing record
            cursor.execute(
                "UPDATE guest_usage SET usage_count = usage_count + 1 WHERE ip_address = ? AND date = ?",
                (ip_address, date)
            )
            
            if cursor.rowcount == 0:
                # No existing record, create new one
                cursor.execute(
                    "INSERT INTO guest_usage (ip_address, date, usage_count) VALUES (?, ?, 1)",
                    (ip_address, date)
                )
                new_count = 1
            else:
                # Get updated count
                cursor.execute(
                    "SELECT usage_count FROM guest_usage WHERE ip_address = ? AND date = ?",
                    (ip_address, date)
                )
                new_count = cursor.fetchone()["usage_count"]
            
            conn.commit()
            conn.close()
            
            print(f"📊 Guest usage incremented: {ip_address} = {new_count}/3")
            return new_count
            
        except Exception as e:
            print(f"❌ Increment guest usage error: {e}")
            return 1

# Global database instance
db = Database()