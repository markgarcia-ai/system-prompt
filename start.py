#!/usr/bin/env python3
"""
Simple startup script for debugging and testing the application
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # Test imports
        print("Testing imports...")
        from app.models import User, Prompt, Purchase, Tag, PromptTag, PromptWatermark, Analytics, Bundle, BundlePrompt, PromptOutput
        print("✓ All models imported successfully")
        
        from app.routes import auth, prompts, purchases, dashboard, tags, outputs, search, analytics, bundles, uploads, webhooks
        print("✓ All routes imported successfully")
        
        from app.main import app
        print("✓ FastAPI app created successfully")
        
        print("\n🎉 All imports successful! The application should start without issues.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 