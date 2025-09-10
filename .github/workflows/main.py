# Placeholder main.py
import os
print("Script started!")
chat_id = os.getenv('CHAT_ID')
message = os.getenv('USER_MESSAGE')
print(f"Received message: '{message}' for chat ID: {chat_id}")
