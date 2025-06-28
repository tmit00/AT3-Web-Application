import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
from datetime import datetime
from data import db, Task
from flask import session

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
    
    def get_user_email(self):
        """Get the current user's email from session"""
        return session.get('user', {}).get('email', 'anonymous@example.com')
    
    def parse_task_action(self, message):
        """
        Parse user message to detect task-related actions
        
        Args:
            message (str): User's message
            
        Returns:
            dict: Action details or None if no action detected
        """
        message_lower = message.lower()
        
        # Create task patterns
        create_patterns = [
            r'create\s+(?:a\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'add\s+(?:a\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'new\s+task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'task\s+(?:called\s+)?["\']?([^"\']+)["\']?'
        ]
        
        # Delete task patterns
        delete_patterns = [
            r'delete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'remove\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'delete\s+task\s+(\d+)',
            r'remove\s+task\s+(\d+)'
        ]
        
        # Complete task patterns
        complete_patterns = [
            r'complete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'mark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?\s+as\s+complete',
            r'finish\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'complete\s+task\s+(\d+)',
            r'mark\s+task\s+(\d+)\s+as\s+complete'
        ]
        
        # Incomplete task patterns
        incomplete_patterns = [
            r'uncomplete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'mark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?\s+as\s+incomplete',
            r'unmark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'uncomplete\s+task\s+(\d+)',
            r'mark\s+task\s+(\d+)\s+as\s+incomplete'
        ]
        
        # Check for create task
        for pattern in create_patterns:
            match = re.search(pattern, message_lower)
            if match:
                title = match.group(1).strip()
                # Extract description and date if provided
                description = None
                date_obj = None
                
                # Look for description after "description:" or "desc:"
                desc_match = re.search(r'description[:\s]+([^,]+)', message, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1).strip()
                
                # Look for date patterns
                date_match = re.search(r'date[:\s]+(\d{4}-\d{2}-\d{2})', message)
                if date_match:
                    try:
                        date_obj = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                    except:
                        pass
                
                return {
                    'action': 'create',
                    'title': title,
                    'description': description,
                    'date': date_obj
                }
        
        # Check for delete task
        for pattern in delete_patterns:
            match = re.search(pattern, message_lower)
            if match:
                identifier = match.group(1).strip()
                return {
                    'action': 'delete',
                    'identifier': identifier
                }
        
        # Check for complete task
        for pattern in complete_patterns:
            match = re.search(pattern, message_lower)
            if match:
                identifier = match.group(1).strip()
                return {
                    'action': 'complete',
                    'identifier': identifier
                }
        
        # Check for incomplete task
        for pattern in incomplete_patterns:
            match = re.search(pattern, message_lower)
            if match:
                identifier = match.group(1).strip()
                return {
                    'action': 'incomplete',
                    'identifier': identifier
                }
        
        return None
    
    def execute_task_action(self, action_data):
        """
        Execute the parsed task action
        
        Args:
            action_data (dict): Action details from parse_task_action
            
        Returns:
            str: Result message
        """
        user_email = self.get_user_email()
        
        if action_data['action'] == 'create':
            try:
                from task import user_create_task
                task = user_create_task(
                    action_data['title'],
                    action_data['description'],
                    action_data['date']
                )
                return f"✅ Task '{action_data['title']}' has been created successfully!"
            except Exception as e:
                return f"❌ Failed to create task: {str(e)}"
        
        elif action_data['action'] in ['delete', 'complete', 'incomplete']:
            identifier = action_data['identifier']
            
            # Try to find task by ID first, then by title
            task = None
            if identifier.isdigit():
                task = Task.query.get(int(identifier))
            else:
                task = Task.query.filter_by(title=identifier, user_email=user_email).first()
            
            if not task:
                return f"❌ Task '{identifier}' not found."
            
            if task.user_email != user_email:
                return "❌ You don't have permission to modify this task."
            
            try:
                if action_data['action'] == 'delete':
                    from task import user_delete_task
                    user_delete_task(task.id)
                    return f"✅ Task '{task.title}' has been deleted successfully!"
                
                elif action_data['action'] == 'complete':
                    from task import user_mark_complete
                    user_mark_complete(task.id, True)
                    return f"✅ Task '{task.title}' has been marked as complete!"
                
                elif action_data['action'] == 'incomplete':
                    from task import user_mark_complete
                    user_mark_complete(task.id, False)
                    return f"✅ Task '{task.title}' has been marked as incomplete!"
                    
            except Exception as e:
                return f"❌ Failed to {action_data['action']} task: {str(e)}"
        
        return "❌ Unknown action."
    
    def get_user_tasks(self):
        """Get all tasks for the current user"""
        user_email = self.get_user_email()
        tasks = Task.query.filter_by(user_email=user_email).all()
        return tasks
    
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
            # First, check if this is a task action
            action_data = self.parse_task_action(message)
            
            if action_data:
                # Execute the action and return the result
                result = self.execute_task_action(action_data)
                return {
                    'response': result,
                    'is_truncated': False,
                    'full_response': result
                }
            
            # If not an action, check if user is asking about their tasks
            if any(word in message.lower() for word in ['my tasks', 'show tasks', 'list tasks', 'what tasks', 'view tasks']):
                tasks = self.get_user_tasks()
                if not tasks:
                    response = "You don't have any tasks yet. You can create one by saying 'create task [task name]'."
                else:
                    task_list = []
                    for task in tasks:
                        status = "✅" if task.is_complete else "⏳"
                        date_str = f" (Due: {task.date})" if task.date else ""
                        task_list.append(f"{status} {task.title}{date_str}")
                    
                    response = f"Here are your tasks:\n" + "\n".join(task_list)
                
                return {
                    'response': response,
                    'is_truncated': False,
                    'full_response': response
                }
            
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