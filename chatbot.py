import os
import google.generativeai as genai
from dotenv import load_dotenv
import re
from datetime import datetime, date, timedelta
from data import db, Task
from flask import session
import json
from collections import defaultdict

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
        
        # Initialize conversation metadata
        self.conversation_metadata = {
            'start_time': datetime.now(),
            'message_count': 0,
            'actions_performed': [],
            'topics_discussed': []
        }
    
    def get_user_email(self):
        """Get the current user's email from session"""
        return session.get('user', {}).get('email', 'anonymous@example.com')
    
    def get_task_analytics(self):
        """Get comprehensive task analytics for the user"""
        user_email = self.get_user_email()
        tasks = Task.query.filter_by(user_email=user_email).all()
        
        if not tasks:
            return None
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_complete])
        incomplete_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Tasks due today
        today = date.today()
        due_today = [t for t in tasks if t.date == today and not t.is_complete]
        
        # Overdue tasks
        overdue_tasks = [t for t in tasks if t.date and t.date < today and not t.is_complete]
        
        # Tasks due this week
        week_end = today + timedelta(days=7)
        due_this_week = [t for t in tasks if t.date and today <= t.date <= week_end and not t.is_complete]
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'incomplete_tasks': incomplete_tasks,
            'completion_rate': round(completion_rate, 1),
            'due_today': len(due_today),
            'overdue_tasks': len(overdue_tasks),
            'due_this_week': len(due_this_week),
            'due_today_list': due_today,
            'overdue_list': overdue_tasks,
            'due_this_week_list': due_this_week
        }
    
    def get_smart_suggestions(self):
        """Generate smart suggestions based on user's task patterns and current state"""
        analytics = self.get_task_analytics()
        if not analytics:
            return ["Create your first task to get started!"]
        
        suggestions = []
        
        # Overdue tasks
        if analytics['overdue_tasks'] > 0:
            suggestions.append(f"⚠️ You have {analytics['overdue_tasks']} overdue task(s). Consider completing them soon.")
        
        # Tasks due today
        if analytics['due_today'] > 0:
            suggestions.append(f"📅 You have {analytics['due_today']} task(s) due today. Focus on these first!")
        
        # Low completion rate
        if analytics['completion_rate'] < 50:
            suggestions.append("📈 Your task completion rate is low. Try breaking down large tasks into smaller ones.")
        
        # No tasks due this week
        if analytics['due_this_week'] == 0 and analytics['incomplete_tasks'] > 0:
            suggestions.append("📋 Consider setting due dates for your incomplete tasks to stay organized.")
        
        # High completion rate
        if analytics['completion_rate'] > 80:
            suggestions.append("🎉 Great job! You're maintaining a high completion rate. Keep it up!")
        
        return suggestions
    
    def extract_task_title(self, raw_title):
        """
        Extract a concise task title from a natural language phrase.
        E.g., 'reminding me to clean the dishes' -> 'clean the dishes'
        """
        # Remove common leading phrases
        patterns = [
            r'^(reminding|remind) (me )?(to )?',
            r'^(i )?need to ',
            r'^(please )?(create|add|make|schedule|set up|start) (a |the |an )?(task|reminder|event)?( for me)?( to)? ',
            r'^(to )?',
        ]
        title = raw_title.strip()
        for pattern in patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE).strip()
        # Remove trailing punctuation
        title = re.sub(r'[.!?]+$', '', title)
        # If the result is empty, fallback to original
        return title if title else raw_title.strip()
    
    def parse_task_action(self, message):
        """
        Parse user message to detect task-related actions with enhanced patterns
        
        Args:
            message (str): User's message
            
        Returns:
            dict: Action details or None if no action detected
        """
        message_lower = message.lower()
        
        # Enhanced delete task patterns (check these FIRST to avoid conflicts)
        delete_patterns = [
            r'delete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'remove\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'delete\s+task\s+(\d+)',
            r'remove\s+task\s+(\d+)',
            r'cancel\s+task\s+["\']?([^"\']+)["\']?',
            r'drop\s+task\s+["\']?([^"\']+)["\']?'
        ]
        
        # Enhanced complete task patterns
        complete_patterns = [
            r'complete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'mark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?\s+as\s+complete',
            r'finish\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'complete\s+task\s+(\d+)',
            r'mark\s+task\s+(\d+)\s+as\s+complete',
            r'done\s+with\s+["\']?([^"\']+)["\']?',
            r'finished\s+["\']?([^"\']+)["\']?'
        ]
        
        # Enhanced incomplete task patterns
        incomplete_patterns = [
            r'uncomplete\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'mark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?\s+as\s+incomplete',
            r'unmark\s+(?:the\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'uncomplete\s+task\s+(\d+)',
            r'mark\s+task\s+(\d+)\s+as\s+incomplete',
            r'reopen\s+task\s+["\']?([^"\']+)["\']?',
            r'undo\s+task\s+["\']?([^"\']+)["\']?'
        ]
        
        # Enhanced create task patterns (check these LAST)
        create_patterns = [
            r'create\s+(?:a\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'add\s+(?:a\s+)?task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'new\s+task\s+(?:called\s+)?["\']?([^"\']+)["\']?',
            r'remind\s+me\s+to\s+([^,]+)',
            r'i\s+need\s+to\s+([^,]+)',
            r'remember\s+to\s+([^,]+)'
        ]
        
        # Check for delete task FIRST (to avoid conflicts)
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
        
        # Check for create task LAST (most general pattern)
        for pattern in create_patterns:
            match = re.search(pattern, message_lower)
            if match:
                raw_title = match.group(1).strip()
                # Use the new extraction function for concise title
                title = self.extract_task_title(raw_title)
                # Extract description and date if provided
                description = None
                date_obj = None
                priority = 'medium'
                
                # Look for description after "description:" or "desc:"
                desc_match = re.search(r'description[:\s]+([^,]+)', message, re.IGNORECASE)
                if desc_match:
                    description = desc_match.group(1).strip()
                
                # Look for date patterns (multiple formats)
                date_patterns = [
                    r'date[:\s]+(\d{4}-\d{2}-\d{2})',
                    r'due[:\s]+(\d{4}-\d{2}-\d{2})',
                    r'by[:\s]+(\d{4}-\d{2}-\d{2})',
                    r'tomorrow',
                    r'next\s+week',
                    r'next\s+month'
                ]
                
                for date_pattern in date_patterns:
                    date_match = re.search(date_pattern, message_lower)
                    if date_match:
                        if date_pattern == r'tomorrow':
                            date_obj = date.today() + timedelta(days=1)
                        elif date_pattern == r'next\s+week':
                            date_obj = date.today() + timedelta(days=7)
                        elif date_pattern == r'next\s+month':
                            date_obj = date.today() + timedelta(days=30)
                        else:
                            try:
                                date_obj = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                            except:
                                pass
                        break
                
                # Look for priority
                if any(word in message_lower for word in ['urgent', 'high priority', 'important']):
                    priority = 'high'
                elif any(word in message_lower for word in ['low priority', 'not urgent']):
                    priority = 'low'
                
                return {
                    'action': 'create',
                    'title': title,
                    'description': description,
                    'date': date_obj,
                    'priority': priority
                }
        
        return None
    
    def execute_task_action(self, action_data):
        """
        Execute the parsed task action with enhanced functionality
        
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
                
                # Log the action
                self.conversation_metadata['actions_performed'].append({
                    'action': 'create',
                    'task_title': action_data['title'],
                    'timestamp': datetime.now().isoformat()
                })
                
                response = f"✅ Task '{action_data['title']}' has been created successfully!"
                
                # Add priority info if specified
                if action_data.get('priority') == 'high':
                    response += "\n🚨 Marked as high priority"
                
                # Add due date info if specified
                if action_data['date']:
                    response += f"\n📅 Due: {action_data['date'].strftime('%B %d, %Y')}"
                
                return response
                
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
                    
                    # Log the action
                    self.conversation_metadata['actions_performed'].append({
                        'action': 'delete',
                        'task_title': task.title,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return f"✅ Task '{task.title}' has been deleted successfully!"
                
                elif action_data['action'] == 'complete':
                    from task import user_mark_complete
                    user_mark_complete(task.id, True)
                    
                    # Log the action
                    self.conversation_metadata['actions_performed'].append({
                        'action': 'complete',
                        'task_title': task.title,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return f"✅ Task '{task.title}' has been marked as complete!"
                
                elif action_data['action'] == 'incomplete':
                    from task import user_mark_complete
                    user_mark_complete(task.id, False)
                    
                    # Log the action
                    self.conversation_metadata['actions_performed'].append({
                        'action': 'incomplete',
                        'task_title': task.title,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    return f"✅ Task '{task.title}' has been marked as incomplete!"
                    
            except Exception as e:
                return f"❌ Failed to {action_data['action']} task: {str(e)}"
        
        return "❌ Unknown action."
    
    def get_user_tasks(self, filter_type=None):
        """Get tasks for the current user with optional filtering"""
        user_email = self.get_user_email()
        tasks = Task.query.filter_by(user_email=user_email).all()
        
        if filter_type == 'completed':
            return [t for t in tasks if t.is_complete]
        elif filter_type == 'incomplete':
            return [t for t in tasks if not t.is_complete]
        elif filter_type == 'overdue':
            today = date.today()
            return [t for t in tasks if t.date and t.date < today and not t.is_complete]
        elif filter_type == 'due_today':
            today = date.today()
            return [t for t in tasks if t.date == today and not t.is_complete]
        elif filter_type == 'due_this_week':
            today = date.today()
            week_end = today + timedelta(days=7)
            return [t for t in tasks if t.date and today <= t.date <= week_end and not t.is_complete]
        
        return tasks
    
    def generate_conversation_summary(self):
        """Generate a summary of the current conversation session"""
        if not self.conversation_metadata['actions_performed']:
            return "No actions performed in this session."
        
        action_counts = defaultdict(int)
        for action in self.conversation_metadata['actions_performed']:
            action_counts[action['action']] += 1
        
        summary = f"📊 **Session Summary**\n"
        summary += f"• Messages exchanged: {self.conversation_metadata['message_count']}\n"
        summary += f"• Actions performed: {len(self.conversation_metadata['actions_performed'])}\n"
        
        if action_counts['create'] > 0:
            summary += f"• Tasks created: {action_counts['create']}\n"
        if action_counts['complete'] > 0:
            summary += f"• Tasks completed: {action_counts['complete']}\n"
        if action_counts['delete'] > 0:
            summary += f"• Tasks deleted: {action_counts['delete']}\n"
        
        return summary
    
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
    
    def truncate_to_word_limit(self, text, word_limit=100):
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
        Send a message to the chatbot and get a response with enhanced functionality
        
        Args:
            message (str): The user's message
            
        Returns:
            dict: Response with truncated text, truncation status, and full text
        """
        try:
            # Update conversation metadata
            self.conversation_metadata['message_count'] += 1
            
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
            
            # Check for analytics requests
            if any(word in message.lower() for word in ['analytics', 'stats', 'statistics', 'progress', 'summary']):
                analytics = self.get_task_analytics()
                if not analytics:
                    response = "You don't have any tasks yet. Create your first task to see analytics!"
                else:
                    response = f"📊 **Task Analytics**\n"
                    response += f"• Total tasks: {analytics['total_tasks']}\n"
                    response += f"• Completed: {analytics['completed_tasks']}\n"
                    response += f"• Incomplete: {analytics['incomplete_tasks']}\n"
                    response += f"• Completion rate: {analytics['completion_rate']}%\n"
                    response += f"• Due today: {analytics['due_today']}\n"
                    response += f"• Overdue: {analytics['overdue_tasks']}\n"
                    response += f"• Due this week: {analytics['due_this_week']}"
                
                return {
                    'response': response,
                    'is_truncated': False,
                    'full_response': response
                }
            
            # Check for suggestions
            if any(word in message.lower() for word in ['suggest', 'suggestion', 'help', 'advice', 'tip']):
                suggestions = self.get_smart_suggestions()
                response = "💡 **Smart Suggestions**\n" + "\n".join(suggestions)
                return {
                    'response': response,
                    'is_truncated': False,
                    'full_response': response
                }
            
            # Check for session summary
            if any(word in message.lower() for word in ['session summary', 'conversation summary', 'what did we do']):
                summary = self.generate_conversation_summary()
                return {
                    'response': summary,
                    'is_truncated': False,
                    'full_response': summary
                }
            
            # Enhanced task listing with filters
            if any(word in message.lower() for word in ['my tasks', 'show tasks', 'list tasks', 'what tasks', 'view tasks']):
                filter_type = None
                if 'completed' in message.lower():
                    filter_type = 'completed'
                elif 'incomplete' in message.lower():
                    filter_type = 'incomplete'
                elif 'overdue' in message.lower():
                    filter_type = 'overdue'
                elif 'today' in message.lower():
                    filter_type = 'due_today'
                elif 'week' in message.lower():
                    filter_type = 'due_this_week'
                
                tasks = self.get_user_tasks(filter_type)
                if not tasks:
                    if filter_type:
                        response = f"You don't have any {filter_type.replace('_', ' ')} tasks."
                    else:
                        response = "You don't have any tasks yet. You can create one by saying 'create task [task name]'."
                else:
                    filter_text = f" ({filter_type.replace('_', ' ')})" if filter_type else ""
                    task_list = []
                    for task in tasks:
                        status = "✅" if task.is_complete else "⏳"
                        date_str = f" (Due: {task.date.strftime('%B %d, %Y')})" if task.date else ""
                        task_list.append(f"{status} {task.title}{date_str}")
                    
                    response = f"Here are your tasks{filter_text}:\n" + "\n".join(task_list)
                
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
            
            # Truncate the response to 100 words
            truncated_response, is_truncated, full_response = self.truncate_to_word_limit(clean_response, 100)
            
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
        """Clear the conversation history and reset metadata"""
        self.conversation_history = []
        self.conversation_metadata = {
            'start_time': datetime.now(),
            'message_count': 0,
            'actions_performed': [],
            'topics_discussed': []
        }
    
    def get_history(self):
        """Get the current conversation history"""
        return self.conversation_history
    
    def get_metadata(self):
        """Get conversation metadata"""
        return self.conversation_metadata

# Create a global chatbot instance
chatbot_instance = Chatbot()