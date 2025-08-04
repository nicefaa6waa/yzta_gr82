from database.database import db  # For users and guest usage
from database.chat_db import ChatDB  # For encrypted chats
from api_client import medical_api_client  # New API client
from fastapi import FastAPI, HTTPException, Depends, Response, Request, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import jwt
import os
from datetime import datetime, timedelta
import uuid
import bcrypt
import aiofiles

app = FastAPI(title="RadiGlow API", description="Medical AI Chat Platform")

# FIXED: Custom StaticFiles class to disable caching
class NoCacheStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        # Disable caching for CSS, JS, and other static files
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

# Mount static files with no caching
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize both databases
db.init_db()  # User authentication database
chat_db = ChatDB()  # Encrypted chat database

# Security
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24  # 30 days

# Add the missing security instance
security = HTTPBearer()

# Models
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ChatMessage(BaseModel):
    message: str
    chat_id: Optional[str] = None

class GuestMessage(BaseModel):
    message: str

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_from_cookie(request: Request):
    token = request.cookies.get('token')
    if not token:
        raise HTTPException(status_code=401, detail="No token found")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_index():
    return FileResponse('static/index.html')

@app.get("/chat", response_class=HTMLResponse)
async def read_chat(request: Request):
    token = request.cookies.get('token')
    if not token:
        return RedirectResponse(url='/', status_code=302)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email or not db.get_user_by_email(email):
            return RedirectResponse(url='/', status_code=302)
    except Exception as e:
        print(f"Auth error: {e}")
        return RedirectResponse(url='/', status_code=302)
    
    return FileResponse('static/chat.html')

@app.post("/api/register")
async def register(user: UserRegister, response: Response):
    result = db.create_user(user.email, user.name, user.password)
    if not result:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    access_token = create_access_token(data={"sub": user.email})
    
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite='lax',
        max_age=1800
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": result}

@app.post("/api/login")
async def login(user: UserLogin, response: Response):
    result = db.authenticate_user(user.email, user.password)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email})
    
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite='lax',
        max_age=1800
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": result
    }

@app.get("/api/user/chats")
async def get_user_chats(request: Request):
    current_user = get_current_user_from_cookie(request)
    user = db.get_user_by_email(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    chats = chat_db.get_user_chats(str(user["id"]))
    return chats

@app.get("/api/chat/{chat_id}")
async def get_chat(chat_id: str, request: Request):
    try:
        current_user = get_current_user_from_cookie(request)
        user = db.get_user_by_email(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_key = chat_db.get_user_key(str(user["id"]), user["email"])
        chat_history = chat_db.get_chat_history(chat_id, user_key)
        
        return {
            "id": chat_id,
            "title": f"Chat {chat_id[:8]}...",
            "created_at": datetime.now().isoformat(),
            "messages": chat_history
        }
    except Exception as e:
        print(f"Get chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/guest")
async def guest_chat(message: GuestMessage, request: Request):
    client_ip = request.client.host
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    current_usage = db.get_guest_usage(client_ip, current_date)
    if current_usage >= 3:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Daily limit reached. Please sign up for unlimited access.",
                "type": "usage_limit",
                "remaining": 0,
                "total": 3
            }
        )

    try:
        usage_count = db.increment_guest_usage(client_ip, current_date)
        
        # Use the medical API client for guest messages (text-only, will use Gemini)
        api_response = await medical_api_client.process_message(message.message, max_tokens=500)

        return {
            "message": message.message,
            "response": api_response['response'],
            "remaining": max(3 - usage_count, 0),
            "total": 3,
            "model": api_response.get('model', 'AI Assistant')
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"message": str(e), "type": "error"}
        )

@app.post("/api/chat/send")
async def send_message(message: ChatMessage, request: Request):
    try:
        current_user = get_current_user_from_cookie(request)
        user = db.get_user_by_email(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id = str(user["id"])
        user_key = chat_db.get_user_key(user_id, user["email"])
        
        chat_id = message.chat_id
        is_new_chat = False
        
        # Only create new chat if chat_id is None or empty
        if not chat_id:
            title = message.message[:30] + "..." if len(message.message) > 30 else message.message
            chat_id = chat_db.create_chat(user_id, title)
            is_new_chat = True
        
        # Add user message
        chat_db.add_message(chat_id, message.message, "user", user_id, user_key)
        
        # Use the medical API client to generate response (text-only, will use Gemini)
        api_response = await medical_api_client.process_message(message.message, max_tokens=500)
        
        # Add AI response
        chat_db.add_message(chat_id, api_response['response'], "assistant", user_id, user_key)
        
        # Get complete chat history
        chat_history = chat_db.get_chat_history(chat_id, user_key)
        
        return {
            "id": chat_id,
            "title": message.message[:30] + "..." if len(message.message) > 30 else message.message,
            "messages": chat_history,
            "created_at": datetime.now().isoformat(),
            "is_new_chat": is_new_chat
        }

    except Exception as e:
        print(f"Send message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/upload")
async def upload_image(file: UploadFile = File(...), text: str = "", chat_id: str = "", request: Request = None):
    """Handle image upload for medical analysis - treat exactly like text messages"""
    try:
        current_user = get_current_user_from_cookie(request)
        user = db.get_user_by_email(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        user_id = str(user["id"])
        user_key = chat_db.get_user_key(user_id, user["email"])
        
        # CRITICAL FIX: Handle chat continuation EXACTLY like text messages
        if chat_id and chat_id.strip() and chat_id != "null" and chat_id != "undefined":
            # Continue existing chat - this is the key fix
            existing_chat_id = chat_id.strip()
            try:
                # IMPORTANT: Verify the chat exists and belongs to this user
                existing_messages = chat_db.get_chat_history(existing_chat_id, user_key)
                print(f"✅ CONTINUING existing chat: {existing_chat_id} with {len(existing_messages)} existing messages")
                is_new_chat = False
                
                # Make sure we're using the EXACT same chat ID
                chat_id_to_use = existing_chat_id
                
            except Exception as e:
                print(f"❌ Chat verification failed for {existing_chat_id}: {e}")
                raise HTTPException(status_code=404, detail="Chat not found or access denied")
        else:
            # Create new chat only if no valid chat_id provided
            if text.strip():
                title = text[:30] + "..." if len(text) > 30 else text
            else:
                title = f"Image Analysis - {file.filename}"
            chat_id_to_use = chat_db.create_chat(user_id, title)
            is_new_chat = True
            print(f"✅ CREATED new chat: {chat_id_to_use}")
        
        # FIXED: Show user's actual input, not default message
        if text.strip():
            user_message = text.strip()
            print(f"✅ Using user's EXACT text: '{user_message}'")
        else:
            user_message = f"Uploaded image: {file.filename}"
            print(f"✅ Using image upload message: '{user_message}'")
        
        # Add user message to the chat (using the SAME chat ID)
        message_id = chat_db.add_message(chat_id_to_use, user_message, "user", user_id, user_key)
        print(f"✅ Added user message ID: {message_id} to chat: {chat_id_to_use}")
        
        # Process image with medical API
        api_prompt = text.strip() if text.strip() else "Please analyze this medical image and provide detailed insights."
        api_response = await medical_api_client.process_message(
            api_prompt,
            image_data=image_data,
            max_tokens=500
        )
        
        # Add AI response to the SAME chat
        ai_message_id = chat_db.add_message(chat_id_to_use, api_response['response'], "assistant", user_id, user_key)
        print(f"✅ Added AI response ID: {ai_message_id} to chat: {chat_id_to_use}")
        
        # Get complete chat history INCLUDING all previous messages
        chat_history = chat_db.get_chat_history(chat_id_to_use, user_key)
        print(f"✅ Final chat {chat_id_to_use} has {len(chat_history)} total messages")
        
        # CRITICAL: Return the EXACT same format as text messages
        return {
            "id": chat_id_to_use,  # Use the same chat ID that was passed in
            "title": text[:30] + "..." if text and len(text) > 30 else f"Image Analysis - {file.filename}",
            "messages": chat_history,  # ALL messages including previous ones
            "created_at": datetime.now().isoformat(),
            "is_new_chat": is_new_chat
        }
        
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guest/usage")
async def get_guest_usage(request: Request):
    client_ip = request.client.host
    current_date = datetime.now().strftime("%Y-%m-%d")
    usage_count = db.get_guest_usage(client_ip, current_date)
    remaining = max(3 - usage_count, 0)
    return {
        "remaining": remaining,
        "total": 3,
        "can_use": remaining > 0
    }

@app.delete("/api/chat/{chat_id}")
async def delete_chat(chat_id: str, request: Request):
    try:
        current_user = get_current_user_from_cookie(request)
        user = db.get_user_by_email(current_user)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete chat from encrypted database
        success = chat_db.delete_chat(chat_id, str(user["id"]))
        if not success:
            raise HTTPException(status_code=404, detail="Chat not found or not authorized")
        
        return {"message": "Chat deleted successfully"}
    except Exception as e:
        print(f"Delete chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)