import logging
import traceback
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

print("Initializing model...")
model = genai.GenerativeModel('gemini-1.5-flash')
print("Model initialized. Calling API...")
try:
    response = model.generate_content('Hello')
    print("Response:", response.text)
except Exception as e:
    print("Exception occurred:")
    print(traceback.format_exc())
