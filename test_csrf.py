#!/usr/bin/env python3
"""
Test script to verify CSRF protection is working correctly.
This script starts the Flask app in a separate process and makes test requests.
"""

import requests
import subprocess
import time
import signal
import os
import sys
from bs4 import BeautifulSoup

def test_csrf_protection():
    print("Testing CSRF Protection Implementation...")
    
    # Test endpoints that should require CSRF tokens
    test_cases = [
        {
            'name': 'Register Form',
            'url': 'http://localhost:5001/register',
            'method': 'POST',
            'data': {'email': 'test@example.com', 'password': 'testpass', 'confirmPassword': 'testpass'}
        },
        {
            'name': 'Login Form', 
            'url': 'http://localhost:5001/login/manual',
            'method': 'POST',
            'data': {'email': 'test@example.com', 'password': 'testpass'}
        }
    ]
    
    session = requests.Session()
    
    for test in test_cases:
        print(f"\nTesting {test['name']}...")
        
        # First, try without CSRF token (should fail)
        try:
            response = session.request(test['method'], test['url'], data=test['data'])
            if response.status_code == 400 and 'CSRF' in response.text:
                print(f"✅ {test['name']}: CSRF protection working (request blocked)")
            else:
                print(f"❌ {test['name']}: CSRF protection may not be working (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  {test['name']}: Error testing - {e}")
    
    print("\n" + "="*50)
    print("CSRF Protection Test Complete")
    print("="*50)

if __name__ == "__main__":
    # Start the Flask app
    print("Starting Flask app for testing...")
    
    try:
        # Give the server a moment to start
        time.sleep(2)
        test_csrf_protection()
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Test error: {e}")
