#!/usr/bin/env python3
"""
Test script for local LLM models
Verifies that downloaded models can be loaded and used correctly
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Load local environment variables if available
if os.path.exists('local.env'):
    print("📋 Loading local.env configuration...")
    with open('local.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print(f"🔧 USE_LOCAL_MODELS: {os.getenv('USE_LOCAL_MODELS', 'not set')}")
    print(f"🔧 LOCAL_MODELS_PATH: {os.getenv('LOCAL_MODELS_PATH', 'not set')}")

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_model_loading():
    """Test loading each downloaded model"""
    
    try:
        # Import the local LLM service
        from app.services.local_llm_service import LocalLLMService
        
        # Initialize service
        llm_service = LocalLLMService()
        
        # Test models (matching your downloaded structure)
        test_models = [
            "Phi-3-mini-4k-instruct",
            "Qwen2-1.5B-Instruct", 
            "StableLM-Zephyr-3B"
        ]
        
        print("=" * 60)
        print("🤖 TUX LOCAL MODEL VERIFICATION")
        print("=" * 60)
        
        # Check models directory
        models_path = os.getenv("LOCAL_MODELS_PATH", "./models")
        models_dir = Path(models_path)
        if not models_dir.exists():
            print(f"❌ Models directory not found: {models_dir.absolute()}")
            return False
            
        print(f"📁 Models directory: {models_dir.absolute()}")
        
        # List available model folders
        available_models = [d.name for d in models_dir.iterdir() if d.is_dir()]
        print(f"📋 Available model folders: {available_models}")
        
        success_count = 0
        
        for model_name in test_models:
            print(f"\n🔍 Testing model: {model_name}")
            
            # Check if model directory exists
            model_path = models_dir / model_name
            if not model_path.exists():
                print(f"❌ Model directory not found: {model_path}")
                continue
                
            # Check required files
            required_files = ["config.json", "tokenizer.json"]
            missing_files = []
            
            for file_name in required_files:
                if not (model_path / file_name).exists():
                    missing_files.append(file_name)
                    
            if missing_files:
                print(f"❌ Missing required files: {missing_files}")
                continue
                
            # Check model files
            model_files = list(model_path.glob("*.safetensors")) + list(model_path.glob("pytorch_model*.bin"))
            if not model_files:
                print(f"❌ No model weight files found")
                continue
                
            print(f"✅ Model files present: {len(model_files)} weight files")
            
            # Test loading (quick check)
            try:
                print(f"🔄 Attempting to load model...")
                load_success = await llm_service.load_model(model_name, "test")
                
                if load_success:
                    print(f"✅ Model loaded successfully!")
                    
                    # Test simple generation
                    print(f"🧪 Testing text generation...")
                    test_prompt = "Hello, this is a test. Please respond briefly."
                    
                    response = await llm_service.generate_text(
                        prompt=test_prompt,
                        model_name=model_name,
                        max_tokens=50,
                        temperature=0.7
                    )
                    
                    if response and len(response) > 0:
                        print(f"✅ Generation successful!")
                        print(f"📝 Response preview: {response[:100]}...")
                        success_count += 1
                    else:
                        print(f"❌ Generation failed - empty response")
                        
                    # Unload model to free memory
                    await llm_service.unload_model(model_name)
                    print(f"🗑️  Model unloaded")
                    
                else:
                    print(f"❌ Failed to load model")
                    
            except Exception as e:
                print(f"❌ Error testing model: {str(e)}")
                
        print(f"\n" + "=" * 60)
        print(f"🎯 SUMMARY: {success_count}/{len(test_models)} models working correctly")
        
        if success_count == len(test_models):
            print("🎉 All models are ready for local deployment!")
            return True
        else:
            print("⚠️  Some models need attention")
            return False
            
    except ImportError as e:
        print(f"❌ Import error - dependencies missing: {str(e)}")
        print("💡 Run: pip install transformers torch accelerate")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

async def test_serverless_mode():
    """Test serverless API-only mode"""
    
    print("\n" + "=" * 60)
    print("🚀 TESTING SERVERLESS MODE")
    print("=" * 60)
    
    try:
        # Set environment for serverless mode
        os.environ["USE_LOCAL_MODELS"] = "false"
        
        from app.services.llm_service import LLMService
        
        llm_service = LLMService()
        print("✅ LLM Service initialized in API-only mode")
        print(f"🔧 Local models enabled: {llm_service.use_local_models}")
        
        if not llm_service.use_local_models:
            print("✅ Serverless mode configured correctly")
            print("💡 Will use external APIs when deployed")
            return True
        else:
            print("❌ Serverless mode not configured correctly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing serverless mode: {str(e)}")
        return False

async def main():
    """Run all tests"""
    
    print("🔧 TUX Model Verification Suite")
    print("Testing both local and serverless deployment modes...\n")
    
    # Test serverless mode (current deployment target)
    serverless_ok = await test_serverless_mode()
    
    # Test local models (for future use)
    local_ok = await test_model_loading()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS")
    print("=" * 60)
    print(f"🚀 Serverless Mode: {'✅ Ready' if serverless_ok else '❌ Issues'}")
    print(f"🤖 Local Models: {'✅ Ready' if local_ok else '❌ Issues'}")
    
    if serverless_ok:
        print("\n🎉 TUX is ready for serverless deployment!")
        print("💡 You can deploy immediately with $0 idle costs")
        
    if local_ok:
        print("\n🎉 Local models are ready for future use!")
        print("💡 Set USE_LOCAL_MODELS=true to enable them")
    
    print("\n🚀 Next steps:")
    print("1. Deploy to Railway/Render for serverless hosting")
    print("2. Set up API keys for Together.AI and HuggingFace")
    print("3. Test with real UX generation requests")

if __name__ == "__main__":
    asyncio.run(main()) 