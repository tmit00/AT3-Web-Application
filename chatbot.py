import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Chatbot:
    def __init__(self):
        # Get API key from environment variable or use the one from the original file
        api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyDXf9esb4oJEmIkVaimIUb2aQz8_hbTCeg')
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Initialize chat history
        self.chat_history = []
    
    def send_message(self, message):
        """
        Send a message to the chatbot and get a response
        
        Args:
            message (str): The user's message
            
        Returns:
            str: The chatbot's response
        """
        try:
            # Add user message to history
            self.chat_history.append({"role": "user", "parts": [message]})
            
            # Generate response
            response = self.model.generate_content(message)
            
            # Add assistant response to history
            self.chat_history.append({"role": "assistant", "parts": [response.text]})
            
            return response.text
            
        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            return error_message
    
    def clear_history(self):
        """Clear the chat history"""
        self.chat_history = []
    
    def get_history(self):
        """Get the current chat history"""
        return self.chat_history

# Create a global chatbot instance
chatbot_instance = Chatbot()