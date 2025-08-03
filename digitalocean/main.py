from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
import logging
from typing import Optional
from PIL import Image
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv("API_KEY", "your-api-key")
MODEL_NAME = os.getenv("MODEL_NAME", "churchylol/medgemma-4b-it-merged)
HF_TOKEN = os.getenv("HF_TOKEN")

print(f"🔑 Loaded API Key: {API_KEY[:20]}...{API_KEY[-10:]}")  # Debug line

# Initialize FastAPI app
app = FastAPI(
    title="MedGemma API",
    description="API endpoint for MedGemma model - requires both text and image",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Response model
class InferenceResponse(BaseModel):
    response: str
    model: str
    timestamp: str

# Global variables
model = None
processor = None
device = None

def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Verify API key from header"""
    logger.info(f"🔍 Received API Key: {x_api_key[:20] if x_api_key else 'None'}...{x_api_key[-10:] if x_api_key and len(x_api_key) > 10 else ''}")
    logger.info(f"🔍 Expected API Key: {API_KEY[:20]}...{API_KEY[-10:]}")
    
    if x_api_key != API_KEY:
        logger.error(f"❌ API Key mismatch!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    logger.info("✅ API Key validated successfully")
    return x_api_key

def load_model():
    """Load the MedGemma model and processor"""
    global model, processor, device
    
    try:
        logger.info(f"Loading model: {MODEL_NAME}")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        auth_token = HF_TOKEN if HF_TOKEN else None
        
        # Load processor
        processor = AutoProcessor.from_pretrained(
            MODEL_NAME,
            token=auth_token,
            trust_remote_code=True
        )
        logger.info("✅ Processor loaded")
        
        # Load model with better error handling
        model_kwargs = {
            "token": auth_token,
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        
        if device == "cuda":
            model_kwargs.update({
                "torch_dtype": torch.bfloat16,
                "device_map": "auto",
            })
        else:
            model_kwargs["torch_dtype"] = torch.float32
        
        model = AutoModelForImageTextToText.from_pretrained(MODEL_NAME, **model_kwargs)
        
        if device == "cpu":
            model = model.to(device)
        
        model.eval()
        logger.info("✅ Model loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {str(e)}")
        raise e

@app.on_event("startup")
async def startup_event():
    """Load model on startup"""
    load_model()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "MedGemma API is running", "status": "healthy"}

@app.post("/inference", response_model=InferenceResponse)
async def inference(
    text: str = Form(...),
    image: UploadFile = File(...),
    max_new_tokens: Optional[int] = Form(50),
    api_key: str = Depends(verify_api_key)
):
    """
    Inference endpoint - requires BOTH text and image + valid API key
    
    Args:
        text: Required text input/question
        image: Required image file
        max_new_tokens: Maximum tokens to generate (default: 50)
    """
    if model is None or processor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded"
        )
    
    try:
        # Validate text input
        text = text.strip()
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text input is required"
            )
        
        # Process image (required)
        try:
            image_data = await image.read()
            pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
            logger.info("✅ Image processed")
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format: {str(e)}"
            )
        
        # Create messages in the format expected by MedGemma
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": text}
                ]
            }
        ]
        
        # Apply chat template and tokenize
        try:
            inputs = processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
            )
            
            # Move to device with error handling
            if device == "cuda":
                try:
                    inputs = inputs.to(model.device)
                except Exception as e:
                    logger.error(f"CUDA error moving inputs: {str(e)}")
                    # Fallback to CPU
                    device_cpu = "cpu"
                    model_cpu = model.cpu()
                    inputs = inputs.to("cpu")
                    logger.info("Fallback to CPU processing")
                    
        except Exception as e:
            logger.error(f"Error in chat template: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Template processing failed: {str(e)}"
            )
        
        # Generate response with error handling
        try:
            with torch.no_grad():
                # Clear CUDA cache if using GPU
                if device == "cuda":
                    torch.cuda.empty_cache()
                
                # Use conservative parameters to avoid CUDA errors
                generation_kwargs = {
                    "max_new_tokens": min(max_new_tokens, 100),
                    "do_sample": False,  # Use greedy decoding to avoid sampling errors
                    "pad_token_id": processor.tokenizer.pad_token_id,
                    "eos_token_id": processor.tokenizer.eos_token_id,
                    "use_cache": True,
                }
                
                outputs = model.generate(**inputs, **generation_kwargs)
                
        except RuntimeError as e:
            if "CUDA" in str(e):
                logger.error(f"CUDA error during generation: {str(e)}")
                # Try CPU fallback
                try:
                    logger.info("Attempting CPU fallback...")
                    model_cpu = model.cpu()
                    inputs_cpu = {k: v.cpu() for k, v in inputs.items()}
                    
                    with torch.no_grad():
                        outputs = model_cpu.generate(
                            **inputs_cpu,
                            max_new_tokens=min(max_new_tokens, 50),
                            do_sample=False,
                            pad_token_id=processor.tokenizer.pad_token_id,
                        )
                    
                    # Move model back to GPU for next request
                    if torch.cuda.is_available():
                        model.cuda()
                        
                except Exception as cpu_e:
                    logger.error(f"CPU fallback also failed: {str(cpu_e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Both GPU and CPU inference failed"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Generation failed: {str(e)}"
                )
        
        # Decode only the new tokens (response)
        try:
            response_text = processor.decode(
                outputs[0][inputs["input_ids"].shape[-1]:], 
                skip_special_tokens=True
            ).strip()
        except Exception as e:
            logger.error(f"Decoding error: {str(e)}")
            response_text = "I processed your request but had trouble generating a response. Please try again."
        
        # Ensure we have a response
        if not response_text or len(response_text) < 3:
            response_text = "I analyzed your image and question, but couldn't generate a detailed response. Please try rephrasing your question."
        
        return InferenceResponse(
            response=response_text,
            model=MODEL_NAME,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during inference: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    
    uvicorn.run(app, host=host, port=port)
