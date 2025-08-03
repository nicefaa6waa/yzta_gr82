import os
import requests
from typing import Optional, Dict, Any
import tempfile
import base64
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import Gemini, but don't fail if it's not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

class MedicalAPIClient:
    def __init__(self):
        self.medical_api_url = os.getenv('MEDICAL_API_URL')
        self.medical_api_key = os.getenv('MEDICAL_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        # Configure Gemini only if available and API key exists
        if GEMINI_AVAILABLE and self.gemini_api_key and self.gemini_api_key != 'your_gemini_api_key_here':
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Use the correct model name
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini API configured successfully")
            except Exception as e:
                print(f"⚠️ Gemini API configuration failed: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None
            if not GEMINI_AVAILABLE:
                print("⚠️ Gemini not available - install google-generativeai")
            elif not self.gemini_api_key or self.gemini_api_key == 'your_gemini_api_key_here':
                print("⚠️ Gemini API key not configured")
    
    async def process_message(self, text: str, image_data: Optional[bytes] = None, max_tokens: int = 150) -> Dict[str, Any]:
        """
        Process a message with optional image using the medical API or Gemini fallback
        """
        try:
            # If image is provided, use the medical API
            if image_data and self.medical_api_url and self.medical_api_key:
                return await self._call_medical_api(text, image_data, max_tokens)
            
            # For text-only requests, use Gemini as fallback
            elif self.gemini_model:
                return await self._call_gemini_api(text, max_tokens)
            
            # If neither API is available, return a mock response
            else:
                return self._mock_response(text)
                
        except Exception as e:
            print(f"API Error: {e}")
            return self._mock_response(text, error=str(e))
    
    async def _call_medical_api(self, text: str, image_data: bytes, max_tokens: int) -> Dict[str, Any]:
        """Call the medical API with image and text"""
        try:
            # Create a temporary file for the image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
            
            try:
                # Prepare the request
                headers = {
                    'X-API-Key': self.medical_api_key
                }
                
                files = {
                    'image': open(temp_file_path, 'rb')
                }
                
                data = {
                    'text': text,
                    'max_new_tokens': max_tokens
                }
                
                # Make the API call
                response = requests.post(
                    self.medical_api_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'response': result.get('response', 'No response received'),
                        'model': result.get('model', 'Medical API'),
                        'timestamp': result.get('timestamp', datetime.now().isoformat()),
                        'type': 'medical_api'
                    }
                else:
                    raise Exception(f"API returned status {response.status_code}: {response.text}")
                    
            finally:
                # Clean up the temporary file
                files['image'].close()
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"Medical API call failed: {e}")
    
    async def _call_gemini_api(self, text: str, max_tokens: int) -> Dict[str, Any]:
        """Call Gemini API for text-only requests"""
        try:
            # Create a medical-focused prompt
            medical_prompt = f"""You are a medical AI assistant. Please provide helpful, accurate medical information.

Question: {text}

Please provide a comprehensive but concise medical response. If this is a medical question, include relevant information about symptoms, causes, treatments, or recommendations. If you're unsure about something, please indicate that professional medical consultation is recommended."""

            # Generate response
            response = self.gemini_model.generate_content(medical_prompt)
            
            return {
                'response': response.text,
                'model': 'Gemini Flash',
                'timestamp': datetime.now().isoformat(),
                'type': 'gemini_api'
            }
            
        except Exception as e:
            raise Exception(f"Gemini API call failed: {e}")
    
    def _mock_response(self, text: str, error: Optional[str] = None) -> Dict[str, Any]:
        """Generate a mock response when APIs are unavailable"""
        if error:
            # Don't show technical errors to users
            response_text = "I apologize, but I'm experiencing technical difficulties. Please try again later or consult with a healthcare professional for medical advice."
        else:
            response_text = f"Thank you for your question: '{text}'. I understand you're seeking medical information. While I'm currently operating in demo mode, I recommend consulting with a qualified healthcare professional for accurate medical advice and diagnosis."
        
        return {
            'response': response_text,
            'model': 'Mock Response',
            'timestamp': datetime.now().isoformat(),
            'type': 'mock'
        }

# Global instance
medical_api_client = MedicalAPIClient()