import sqlite3
import hashlib
import uuid
from datetime import datetime
from typing import Optional, List, Dict
import json
from passlib.context import CryptContext
import os

class Database:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def __init__(self):
        # Use absolute path to ensure database location is consistent
        self.db_path = os.path.join(os.path.dirname(__file__), '..', 'radiglow.db')
        self.init_db()
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
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
                UNIQUE(ip_address, date)
            );
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, email: str, name: str, password: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        if self.get_user_by_email(email):
            conn.close()
            return None
        
        # Hash password before storing
        hashed_password = self.pwd_context.hash(password)
        
        cursor.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
            (email, name, hashed_password)
        )
        
        conn.commit()
        conn.close()
        
        return self.get_user_by_email(email)

    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, email, name, password_hash FROM users WHERE email = ?",
            (email,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user and self.pwd_context.verify(password, user["password_hash"]):
            return {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"]
            }
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
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
    
    def get_guest_usage(self, ip_address: str, date: str) -> int:
        """Get guest usage count for today"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT usage_count FROM guest_usage WHERE ip_address = ? AND date = ?",
            (ip_address, date)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result["usage_count"] if result else 0
    
    def increment_guest_usage(self, ip_address: str, date: str) -> int:
        """Increment guest usage count"""
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
        return new_count

# Global database instance
db = Database()