import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

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
        
        # Initialize conversation history
        self.conversation_history = []
    
    def strip_markdown(self, text):
        """
        Remove markdown formatting from text
        
        Args:
            text (str): Text with markdown formatting
            
        Returns:
            str: Clean text without markdown
        """
        # Remove bold formatting (**text** or __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Remove italic formatting (*text* or _text_)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove code formatting (`text`)
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        # Remove strikethrough formatting (~~text~~)
        text = re.sub(r'~~(.*?)~~', r'\1', text)
        
        # Remove headers (# ## ### etc.)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove list markers (- * +)
        text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
        
        # Remove numbered list markers (1. 2. etc.)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def truncate_to_word_limit(self, text, word_limit=150):
        """
        Truncate text to a specific word limit
        
        Args:
            text (str): The text to truncate
            word_limit (int): Maximum number of words
            
        Returns:
            tuple: (truncated_text, is_truncated, full_text)
        """
        words = text.split()
        if len(words) <= word_limit:
            return text, False, text
        
        # Truncate to word limit
        truncated_words = words[:word_limit]
        truncated_text = ' '.join(truncated_words)
        
        # Add ellipsis if truncated
        if not truncated_text.endswith('.'):
            truncated_text += '...'
        
        return truncated_text, True, text
    
    def send_message(self, message):
        """
        Send a message to the chatbot and get a response
        
        Args:
            message (str): The user's message
            
        Returns:
            dict: Response with truncated text, truncation status, and full text
        """
        try:
            # Add user message to conversation history
            self.conversation_history.append({"role": "user", "parts": [message]})
            
            # Create the full conversation context
            conversation = self.conversation_history.copy()
            
            # Generate response with full conversation context
            response = self.model.generate_content(conversation)
            
            # Clean the response by removing markdown formatting
            clean_response = self.strip_markdown(response.text)
            
            # Truncate the response to 150 words
            truncated_response, is_truncated, full_response = self.truncate_to_word_limit(clean_response, 150)
            
            # Add assistant response to conversation history (use full response for context)
            self.conversation_history.append({"role": "assistant", "parts": [full_response]})
            
            return {
                'response': truncated_response,
                'is_truncated': is_truncated,
                'full_response': full_response
            }
            
        except Exception as e:
            error_message = f"Sorry, I encountered an error: {str(e)}"
            return {
                'response': error_message,
                'is_truncated': False,
                'full_response': error_message
            }
    
    def clear_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
    
    def get_history(self):
        """Get the current conversation history"""
        return self.conversation_history

# Create a global chatbot instance
chatbot_instance = Chatbot()