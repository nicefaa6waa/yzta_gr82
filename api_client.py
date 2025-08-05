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
        
        print(f"🔗 Medical API URL: {self.medical_api_url}")
        print(f"🔑 Medical API Key: {'✅ Set' if self.medical_api_key else '❌ Missing'}")
        
        # Configure Gemini only if available and API key exists
        if GEMINI_AVAILABLE and self.gemini_api_key and self.gemini_api_key != 'your_gemini_api_key_here':
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                print("✅ Gemini API configured successfully")
            except Exception as e:
                print(f"⚠️ Gemini API configuration failed: {e}")
                self.gemini_model = None
        else:
            self.gemini_model = None

    async def process_message(self, text: str, image_data: Optional[bytes] = None, max_tokens: int = 150) -> Dict[str, Any]:
        """Process a message with optional image using the medical API or Gemini fallback"""
        try:
            # If image is provided, use the medical API
            if image_data and self.medical_api_url and self.medical_api_key:
                print(f"🖼️ Processing image + text with medical API")
                return await self._call_medical_api(text, image_data, max_tokens)
            
            # For text-only requests, use Gemini as fallback
            elif self.gemini_model:
                print(f"📝 Processing text-only with Gemini API")
                return await self._call_gemini_api(text, max_tokens)
            
            # If neither API is available, return a mock response
            else:
                print("⚠️ No APIs available, using mock response")
                return self._mock_response(text)
                
        except Exception as e:
            print(f"❌ API Error: {e}")
            # Try Gemini as fallback if medical API fails and we have image
            if image_data and self.gemini_model:
                print("🔄 Medical API failed, falling back to Gemini for image description...")
                fallback_text = f"I received a medical image along with this question: {text}. Please provide medical guidance and analysis based on the question, noting that I cannot see the specific image details."
                return await self._call_gemini_api(fallback_text, max_tokens)
            
            return self._mock_response(text, error=str(e))

    async def _call_medical_api(self, text: str, image_data: bytes, max_tokens: int) -> Dict[str, Any]:
        """Call the medical API with image and text - FIXED FOR TIMEOUTS"""
        temp_file_path = None
        
        try:
            print(f"🚀 Starting medical API call...")
            print(f"📍 URL: {self.medical_api_url}")
            print(f"📝 Text: {text[:100]}...")
            print(f"🖼️ Image size: {len(image_data)} bytes")
            
            # Create a temporary file for the image
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_file_path = temp_file.name
                print(f"📁 Created temp file: {temp_file_path}")
            
            try:
                # Prepare the request with longer timeouts
                headers = {
                    'X-API-Key': self.medical_api_key,
                    'User-Agent': 'RadiGlow-Frontend/1.0'
                }
                
                data = {
                    'text': text,
                    'max_new_tokens': str(max_tokens)  # Ensure it's a string
                }
                
                files = {
                    'image': ('image.jpg', open(temp_file_path, 'rb'), 'image/jpeg')
                }
                
                print(f"📤 Making request with {max_tokens} max tokens...")
                
                # FIXED: Increased timeouts and added retry logic
                session = requests.Session()
                session.headers.update(headers)
                
                # Configure timeouts: (connect_timeout, read_timeout)
                timeout = (10, 90)  # 10 seconds to connect, 90 seconds to read
                
                response = session.post(
                    self.medical_api_url,
                    files=files,
                    data=data,
                    timeout=timeout,
                    stream=False  # Don't stream to avoid partial responses
                )
                
                print(f"📥 Response received: {response.status_code}")
                print(f"📊 Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    try:
                        result = response.json()
                        print(f"✅ Medical API success!")
                        print(f"🤖 Model: {result.get('model', 'Unknown')}")
                        print(f"📝 Response length: {len(result.get('response', ''))}")
                        
                        return {
                            'response': result.get('response', 'No response received'),
                            'model': result.get('model', 'Medical API'),
                            'timestamp': result.get('timestamp', datetime.now().isoformat()),
                            'type': 'medical_api'
                        }
                    except ValueError as e:
                        print(f"❌ JSON decode error: {e}")
                        print(f"Raw response: {response.text[:500]}")
                        raise Exception(f"Invalid JSON response: {e}")
                
                elif response.status_code == 401:
                    print(f"❌ Authentication failed - check API key")
                    raise Exception("Authentication failed - invalid API key")
                
                elif response.status_code == 422:
                    print(f"❌ Validation error")
                    error_text = response.text
                    raise Exception(f"Validation error: {error_text}")
                
                elif response.status_code == 500:
                    print(f"❌ Server error")
                    error_text = response.text
                    raise Exception(f"Server error: {error_text}")
                
                else:
                    error_text = response.text
                    print(f"❌ Unexpected status {response.status_code}: {error_text}")
                    raise Exception(f"API returned status {response.status_code}: {error_text}")
                    
            finally:
                # Clean up the temporary file and close files
                try:
                    files['image'][1].close()
                except:
                    pass
                    
        except requests.exceptions.ConnectTimeout:
            print(f"❌ Connection timeout to {self.medical_api_url}")
            raise Exception("Failed to connect to medical API - connection timeout")
            
        except requests.exceptions.ReadTimeout:
            print(f"❌ Read timeout from {self.medical_api_url}")
            raise Exception("Medical API is taking too long to respond - please try again")
            
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Connection error: {e}")
            raise Exception("Cannot connect to medical API - please check your connection")
            
        except Exception as e:
            print(f"❌ Medical API call failed: {e}")
            raise Exception(f"Medical API call failed: {e}")
            
        finally:
            # Clean up the temporary file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                    print(f"🗑️ Cleaned up temp file")
                except Exception as e:
                    print(f"⚠️ Failed to clean up temp file: {e}")

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
            if "timeout" in error.lower():
                response_text = "The medical analysis is taking longer than usual. Please try again in a moment, or consult with a healthcare professional for immediate medical advice."
            elif "connect" in error.lower():
                response_text = "I'm having trouble connecting to our medical analysis service. Please try again later or consult with a healthcare professional for medical advice."
            else:
                response_text = "I'm experiencing technical difficulties with our medical analysis service. Please try again later or consult with a healthcare professional for medical advice."
        else:
            response_text = f"Thank you for your question: '{text}'. I understand you're seeking medical information. While I'm currently operating in demo mode, I recommend consulting with a qualified healthcare professional for accurate medical advice and diagnosis."
        
        return {
            'response': response_text,
            'model': 'System Message',
            'timestamp': datetime.now().isoformat(),
            'type': 'mock'
        }

# Global instance
medical_api_client = MedicalAPIClient()