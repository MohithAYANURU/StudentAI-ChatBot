"""
config.py loads all the environment variables in one place
"""


import os
from dotenv import load_dotenv  

load_dotenv()  

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')


#Flask secret key
SECRET_KEY = os.getenv('SECRET_KEY' , "fallback_secret_key")

#llm settings
GROQ_MODEL    = "llama-3.1-8b-instant"
GEMINI_MODEL  = "gemini-2.0-flash"
MISTRAL_MODEL = "mistral-small-latest"
MAX_TOKENS    = 1024

