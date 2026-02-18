import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 1. Browser Settings
    # True - brower runs in background; False - browser window is visible
    HEADLESS = True
    TIMEOUT = 30000 
    
    # 2. The Human Mask
    # Makes the browser appear more like a real user
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    
    # 3. Model Name
    MODEL_NAME = "gemini-3.0-flash-preview"