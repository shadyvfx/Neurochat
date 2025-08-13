import os
from flask import request, jsonify, render_template, session, current_app
from .models import db, User
from . import auth
import openai
from decouple import config
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import base64

# Encryption setup
def get_encryption_key():
    """Get or generate encryption key for message encryption"""
    key = config('ENCRYPTION_KEY', default=None)
    if not key:
        # Generate a new key if none exists
        raw_key = Fernet.generate_key()
        # Remove base64 padding for cleaner storage
        clean_key = raw_key.decode().rstrip('=')
        print(f"Generated new encryption key: {clean_key}")
        print("IMPORTANT: Save this key to your .env file as ENCRYPTION_KEY")
        return raw_key  # Return the original bytes for Fernet
    else:
        # Convert string key back to bytes, adding padding if needed
        if len(key) % 4 != 0:
            key += '=' * (4 - len(key) % 4)
        try:
            return base64.b64decode(key)
        except Exception as e:
            print(f"Invalid encryption key format: {e}")
            # Generate a new key if the provided one is invalid
            raw_key = Fernet.generate_key()
            clean_key = raw_key.decode().rstrip('=')
            print(f"Generated new encryption key: {clean_key}")
            print("IMPORTANT: Save this key to your .env file as ENCRYPTION_KEY")
            return raw_key

def encrypt_message(message):
    """Encrypt a message using Fernet symmetric encryption"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted_message = f.encrypt(message.encode())
        return base64.b64encode(encrypted_message).decode()
    except Exception as e:
        print(f"Encryption error: {e}")
        return message  # Fallback to plain text if encryption fails

def decrypt_message(encrypted_message):
    """Decrypt an encrypted message"""
    try:
        key = get_encryption_key()
        f = Fernet(key)
        # Decode from base64 first
        encrypted_bytes = base64.b64decode(encrypted_message.encode())
        decrypted_message = f.decrypt(encrypted_bytes)
        return decrypted_message.decode()
    except Exception as e:
        print(f"Decryption error: {e}")
        return encrypted_message  # Return as-is if decryption fails

def get_decrypted_conversation_history(session):
    """Get conversation history with decrypted messages for display"""
    if 'conversation_history' not in session:
        return []
    
    decrypted_history = []
    for msg in session['conversation_history']:
        if msg.get('encrypted', False):
            decrypted_msg = {
                'role': msg['role'],
                'message': decrypt_message(msg['message']),
                'timestamp': msg.get('timestamp', None)
            }
        else:
            # Handle legacy unencrypted messages
            decrypted_msg = {
                'role': msg['role'],
                'message': msg['message'],
                'timestamp': msg.get('timestamp', None)
            }
        decrypted_history.append(decrypted_msg)
    
    return decrypted_history

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request for login
    try:
        print("Login route called")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.get_json()}")
        
        data = request.json or request.form
        email = data.get('email')
        password = data.get('password')
        
        print(f"Email: {email}")
        print(f"Password provided: {'Yes' if password else 'No'}")

        if not email or not password:
            print("Missing email or password")
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        print(f"User found: {user is not None}")

        if not user or not user.check_password(password, current_app.extensions['bcrypt']):
            print("Invalid credentials")
            return jsonify({"error": "Invalid email or password"}), 401

        print("Login successful")
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "email": user.email
            }
        }), 200
           
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An error occurred during login"}), 500

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    # Handle POST request for signup
    try:
        print("=== SIGNUP ROUTE DEBUG ===")
        print("Signup route called")
        print(f"Request method: {request.method}")
        print(f"Request headers: {dict(request.headers)}")
        print(f"Request data: {request.get_json()}")
        print(f"Form data: {request.form}")
        
        data = request.json or request.form
        print(f"Final data object: {data}")
        
        first_name = data.get('first_name')
        email = data.get('email')
        password = data.get('password')
        
        print(f"Extracted values:")
        print(f"  - first_name: '{first_name}' (type: {type(first_name)})")
        print(f"  - email: '{email}' (type: {type(email)})")
        print(f"  - password: '{password}' (type: {type(password)})")
        print(f"  - password length: {len(password) if password else 0}")

        # Check each field individually
        if not first_name:
            print("❌ first_name is missing or empty")
            return jsonify({"error": "First name is required"}), 400
        if not email:
            print("❌ email is missing or empty")
            return jsonify({"error": "Email is required"}), 400
        if not password:
            print("❌ password is missing or empty")
            return jsonify({"error": "Password is required"}), 400

        print("✅ All required fields present")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"❌ Email already exists: {email}")
            return jsonify({"error": "Email already in use"}), 400
        
        print("✅ Email is available")

        print("Creating new user...")
        new_user = User(first_name=first_name, email=email)
        new_user.set_password(password, current_app.extensions['bcrypt'])
        print("✅ User object created and password set")

        db.session.add(new_user)
        print("✅ User added to session")
        
        db.session.commit()
        print("✅ User committed to database")
        
        print("User created successfully")
        return jsonify({"message": "Account created successfully"}), 201
    
    except Exception as e:
        print(f"Signup error: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"error": "An error occurred during signup"}), 500

# Chat routes
@auth.route('/guest/status', methods=['GET'])
def guest_status():
    """Get guest session status and remaining time"""
    if 'guest_start_time' not in session:
        return jsonify({"error": "No guest session"}), 400
    
    guest_elapsed = time.time() - session.get('guest_start_time', 0)
    remaining_time = max(0, 900 - guest_elapsed)  # 15 minutes = 900 seconds
    minutes_remaining = int(remaining_time // 60)
    seconds_remaining = int(remaining_time % 60)
    
    # Check if time just expired and send message if needed
    if remaining_time <= 0 and session.get('guest_mode') == 'guest' and not session.get('guest_expired_notified'):
        # Mark that we've notified about expiration
        session['guest_expired_notified'] = True
        
        # Add expiration message to chat history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        expiration_message = "⏰ Your 15-minute guest session has expired. Please create a free account to continue chatting with Neurochat!"
        
        session['conversation_history'].append({
            "role": "ai",
            "message": expiration_message
        })
        
        return jsonify({
            "guest_mode": session.get('guest_mode'),
            "remaining_time": remaining_time,
            "minutes_remaining": minutes_remaining,
            "seconds_remaining": seconds_remaining,
            "expired": True,
            "expiration_message": expiration_message,
            "show_expiration_message": True
        }), 200
    
    return jsonify({
        "guest_mode": session.get('guest_mode'),
        "remaining_time": remaining_time,
        "minutes_remaining": minutes_remaining,
        "seconds_remaining": seconds_remaining,
        "expired": remaining_time <= 0
    }), 200

@auth.route('/chat/history', methods=['GET'])
def get_chat_history():
    """Get decrypted conversation history for display"""
    try:
        decrypted_history = get_decrypted_conversation_history(session)
        return jsonify({
            "history": decrypted_history,
            "count": len(decrypted_history)
        }), 200
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return jsonify({"error": "Failed to retrieve chat history"}), 500

@auth.route('/chat/start', methods=['POST'])
def start_chat():
    """Initialize chat session and ask for conversation mode preference"""
    session['chat_mode'] = None  # Reset mode
    session['conversation_history'] = []
    
    initial_message = {
        "message": "Hi, I'm Neurochat — your friendly AI companion here to listen or talk whenever you need. Would you prefer me to mainly listen and provide gentle support, or would you like me to actively respond and engage in conversation with you?",
        "options": ["Listen Mode", "Response Mode"],
        "type": "mode_selection"
    }
    
    return jsonify(initial_message), 200

@auth.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@auth.route('/chat/mode', methods=['POST'])
def set_chat_mode():
    """Set the conversation mode based on user preference"""
    try:
        data = request.get_json()
        mode = data.get('mode')
        
        if mode not in ['listen', 'talk']:
            return jsonify({"error": "Invalid mode. Must be 'listen' or 'talk'"}), 400
        
        session['chat_mode'] = mode
        session['conversation_history'] = []
        
        # Send confirmation message based on mode
        if mode == 'listen':
            confirmation = "Perfect! I'm in listening mode now. I'm here to support you - share whatever's on your mind and I'll be here to listen and offer gentle encouragement."
        else:
            confirmation = "Awesome! I'm in talk mode now. I'm excited to chat with you and really engage in conversation. What's on your mind?"
        
        # Add confirmation to conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        session['conversation_history'].append({
            "role": "ai",
            "message": confirmation
        })
        
        print(f"Chat mode set to: {mode}")
        print(f"Session contents after mode set: {dict(session)}")
        
        return jsonify({
            "message": "Mode set successfully, please share what's on your mind!",
            "mode": mode,
            "confirmation": confirmation
        }), 200
        
    except Exception as e:
        print(f"Error setting chat mode: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to set chat mode"}), 500

@auth.route('/chat/message', methods=['POST'])
def chat_message():
    """Process user message and return AI response based on mode"""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Check if user is guest and time has expired
    if session.get('guest_mode') == 'guest':
        guest_elapsed = time.time() - session.get('guest_start_time', 0)
        if guest_elapsed > 900:  # 15 minutes
            # Add expiration message to chat history
            if 'conversation_history' not in session:
                session['conversation_history'] = []
            
            expiration_message = "⏰ Your 15-minute guest session has expired. Please create a free account to continue chatting with Neurochat!"
            
            session['conversation_history'].append({
                "role": "ai",
                "message": expiration_message
            })
            
            return jsonify({
                "message": expiration_message,
                "expired": True,
                "guest_expired": True
            }), 200
    
    mode = session.get('chat_mode')
    if not mode:
        return jsonify({"error": "Chat mode not set"}), 400
    
    print(f"Chat message - Current mode: {mode}")
    print(f"Chat message - Session contents: {dict(session)}")
    
    # Store conversation history
    if 'conversation_history' not in session:
        session['conversation_history'] = []
    
    # Encrypt user message before storing
    encrypted_user_message = encrypt_message(user_message)
    
    session['conversation_history'].append({
        "role": "user",
        "message": encrypted_user_message,
        "encrypted": True
    })
    
    # Generate AI response based on mode
    if mode == 'listen':
        print(f"Chat message - Using LISTEN mode")
        ai_response = generate_listening_response(user_message, session['conversation_history'])
    else:
        print(f"Chat message - Using RESPOND mode")
        ai_response = generate_active_response(user_message, session['conversation_history'])
    
    # Encrypt AI response before storing
    encrypted_ai_response = encrypt_message(ai_response)
    
    session['conversation_history'].append({
        "role": "ai",
        "message": encrypted_ai_response,
        "encrypted": True
    })
    
    return jsonify({"message": ai_response, "mode": mode}), 200

def generate_listening_response(user_message, history):
    """Generate empathetic, validating responses for listen mode using OpenAI"""
    try:
        from openai import OpenAI
        import os
        
        # Try multiple ways to get the API key
        api_key = None
        
        # Method 1: Try config function
        try:
            api_key = config('OPENAI_API_KEY', default=None)
            if api_key:
                # Clean the key - remove any line breaks or extra whitespace
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print(f"Listen Mode - Method 1 (config): {api_key[:20]}... (length: {len(api_key)})")
            else:
                print("Listen Mode - Method 1 (config): No key found")
        except Exception as e:
            print(f"Listen Mode - Method 1 failed: {e}")
        
        # Method 2: Try direct environment variable
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                # Clean the key - remove any line breaks or extra whitespace
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print(f"Listen Mode - Method 2 (os.environ): {api_key[:20]}... (length: {len(api_key)})")
            else:
                print("Listen Mode - Method 2 (os.environ): No key found")
        
        # Method 3: Try loading from .env file manually
        if not api_key:
            try:
                # Look for .env file in project root
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                env_path = os.path.join(project_root, '.env')
                print(f"Listen Mode - Looking for .env at: {env_path}")
                
                if os.path.exists(env_path):
                    print("Listen Mode - .env file found, loading...")
                    with open(env_path, 'r') as f:
                        content = f.read()
                        print(f"Listen Mode - .env file content length: {len(content)}")
                        print(f"Listen Mode - .env file content preview: {content[:200]}...")
                        
                        # Look for OPENAI_API_KEY in the content
                        if 'OPENAI_API_KEY=' in content:
                            # Extract the API key, handling potential line breaks
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                # Handle BOM character and check for OPENAI_API_KEY
                                if line.startswith('OPENAI_API_KEY=') or line.startswith('ï»¿OPENAI_API_KEY='):
                                    # Get the key from this line, removing BOM if present
                                    full_key = line.replace('ï»¿OPENAI_API_KEY=', '').replace('OPENAI_API_KEY=', '').strip()
                                    
                                    # Look for continuation in next lines (up to 5 lines)
                                    for j in range(i+1, min(i+5, len(lines))):
                                        next_line = lines[j].strip()
                                        # If next line doesn't contain '=' and isn't empty, it's likely a continuation
                                        if next_line and not next_line.startswith('#') and '=' not in next_line:
                                            full_key += next_line
                                        else:
                                            # Stop if we hit another key or empty line
                                            break
                                    
                                    api_key = full_key
                                    print(f"Listen Mode - Found API key starting with: {api_key[:20]}...")
                                    break
                            
                            if api_key:
                                os.environ['OPENAI_API_KEY'] = api_key
                                print(f"Listen Mode - API key loaded from .env: {api_key[:20]}...")
                                print(f"Listen Mode - API key full length: {len(api_key)}")
                            else:
                                print("Listen Mode - Failed to extract API key from .env file")
                        else:
                            print("Listen Mode - OPENAI_API_KEY not found in .env file")
                else:
                    print(f"Listen Mode - .env file not found at {env_path}")
            except Exception as e:
                print(f"Listen Mode - Method 3 failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Debug: Check final API key status
        print(f"Listen Mode - Final API Key: {api_key[:20] if api_key else 'None'}...")
        print(f"Listen Mode - API Key length: {len(api_key) if api_key else 0}")
        
        if not api_key:
            print("Listen Mode - No API key found after all methods, returning fallback")
            print("Listen Mode - Make sure OPENAI_API_KEY is set in your environment variables")
            return "I'm here to listen and support you. (Note: OpenAI API key not configured - please add OPENAI_API_KEY to your environment variables)"
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        print("Listen Mode - OpenAI client initialized successfully")
        
        # Build conversation context for ChatGPT
        messages = [
            {
                "role": "system", 
                "content": """You are Neurochat, a warm and empathetic AI companion in 'Listen Mode' where you provide gentle validation and support while mainly listening.

Your personality:
- Warm, empathetic, and supportive
- Focus on validating feelings and providing gentle encouragement
- Keep responses relatively short (1-2 sentences usually)
- Be present and understanding without trying to solve problems
- Use a calm, caring tone

Response style:
- Acknowledge their feelings and experiences
- Provide gentle validation and support
- Encourage them to continue sharing
- Be empathetic but not overly formal
- Focus on listening rather than giving advice

Remember: You're here to listen with empathy and provide gentle support, not to solve problems or give advice."""
            }
        ]
        
        # Add recent conversation history (last 4 messages for context)
        recent_history = history[-4:] if len(history) > 4 else history
        for msg in recent_history:
            if msg.get('role') == 'user':
                messages.append({"role": "user", "content": msg.get('message', '')})
            elif msg.get('role') == 'ai':
                messages.append({"role": "assistant", "content": msg.get('message', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        print(f"Listen Mode - Making OpenAI API call with {len(messages)} messages")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"Listen Mode - OpenAI response received: {ai_response[:50]}...")
        return ai_response
        
    except Exception as e:
        print(f"OpenAI API Error in listen mode: {e}")
        import traceback
        traceback.print_exc()
        return "I'm here to listen and support you. Please continue sharing what's on your mind."

def generate_active_response(user_message, history):
    """Generate responses using OpenAI ChatGPT API"""
    
    try:
        from openai import OpenAI
        import os
        
        # Try multiple ways to get the API key
        api_key = None
        
        # Method 1: Try config function
        try:
            api_key = config('OPENAI_API_KEY', default=None)
            if api_key:
                # Clean the key - remove any line breaks or extra whitespace
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print(f"Active Mode - Method 1 (config): {api_key[:20]}... (length: {len(api_key)})")
            else:
                print("Active Mode - Method 1 (config): No key found")
        except Exception as e:
            print(f"Active Mode - Method 1 failed: {e}")
        
        # Method 2: Try direct environment variable
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                # Clean the key - remove any line breaks or extra whitespace
                api_key = api_key.strip().replace('\n', '').replace('\r', '')
                print(f"Active Mode - Method 2 (os.environ): {api_key[:20]}... (length: {len(api_key)})")
            else:
                print("Active Mode - Method 2 (os.environ): No key found")
        
        # Method 3: Try loading from .env file manually
        if not api_key:
            try:
                # Look for .env file in project root
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                env_path = os.path.join(project_root, '.env')
                print(f"Active Mode - Looking for .env at: {env_path}")
                
                if os.path.exists(env_path):
                    print("Active Mode - .env file found, loading...")
                    with open(env_path, 'r') as f:
                        content = f.read()
                        print(f"Active Mode - .env file content length: {len(content)}")
                        print(f"Active Mode - .env file content preview: {content[:200]}...")
                        
                        # Look for OPENAI_API_KEY in the content
                        if 'OPENAI_API_KEY=' in content:
                            # Extract the API key, handling potential line breaks
                            lines = content.split('\n')
                            for i, line in enumerate(lines):
                                # Handle BOM character and check for OPENAI_API_KEY
                                if line.startswith('OPENAI_API_KEY=') or line.startswith('ï»¿OPENAI_API_KEY='):
                                    # Get the key from this line, removing BOM if present
                                    full_key = line.replace('ï»¿OPENAI_API_KEY=', '').replace('OPENAI_API_KEY=', '').strip()
                                    
                                    # Look for continuation in next lines (up to 5 lines)
                                    for j in range(i+1, min(i+5, len(lines))):
                                        next_line = lines[j].strip()
                                        # If next line doesn't contain '=' and isn't empty, it's likely a continuation
                                        if next_line and not next_line.startswith('#') and '=' not in next_line:
                                            full_key += next_line
                                        else:
                                            # Stop if we hit another key or empty line
                                            break
                                    
                                    api_key = full_key
                                    print(f"Active Mode - Found API key starting with: {api_key[:20]}...")
                                    break
                            
                            if api_key:
                                os.environ['OPENAI_API_KEY'] = api_key
                                print(f"Active Mode - API key loaded from .env: {api_key[:20]}...")
                                print(f"Active Mode - API key full length: {len(api_key)}")
                            else:
                                print("Active Mode - Failed to extract API key from .env file")
                        else:
                            print("Active Mode - OPENAI_API_KEY not found in .env file")
                else:
                    print(f"Active Mode - .env file not found at {env_path}")
            except Exception as e:
                print(f"Active Mode - Method 3 failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Debug: Check final API key status
        print(f"Active Mode - Final API Key: {api_key[:20] if api_key else 'None'}...")
        print(f"Active Mode - API Key length: {len(api_key) if api_key else 0}")
        
        if not api_key:
            print("Active Mode - No API key found after all methods, returning fallback")
            print("Active Mode - Make sure OPENAI_API_KEY is set in your environment variables")
            return "I'm here to chat with you! What's on your mind? (Note: OpenAI API key not configured - please add OPENAI_API_KEY to your environment variables)"
        
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        print("Active Mode - OpenAI client initialized successfully")
        
        # Build conversation context for ChatGPT
        messages = [
            {
                "role": "system", 
                "content": """You are Neurochat, a warm and empathetic AI companion in 'Response Mode' where you actively engage in conversation. 

Your personality:
- Casual, friendly, and conversational (like texting a close friend)
- Use natural language, contractions, and sometimes casual expressions
- Be genuinely curious and engaged
- Share relatable thoughts and observations
- Ask follow-up questions when appropriate, but don't make every response a question
- Keep responses relatively short (1-3 sentences usually)
- Be empathetic but not overly formal or therapeutic

Response style:
- Use lowercase naturally when it fits the casual tone
- Occasional casual expressions like "oh wow", "that's wild", "honestly", etc.
- Relate to their experiences with your own observations about life
- Be authentic and human-like, not robotic or overly positive
- Sometimes just validate their feelings without trying to "fix" anything

Remember: You're a supportive friend having a natural conversation, not a therapist or formal assistant."""
            }
        ]
        
        # Add recent conversation history (last 6 messages for context)
        recent_history = history[-6:] if len(history) > 6 else history
        for msg in recent_history:
            if msg.get('role') == 'user':
                messages.append({"role": "user", "content": msg.get('message', '')})
            elif msg.get('role') == 'ai':
                messages.append({"role": "assistant", "content": msg.get('message', '')})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        print(f"Active Mode - Making OpenAI API call with {len(messages)} messages")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.8,
            frequency_penalty=0.3,
            presence_penalty=0.3
        )
        
        ai_response = response.choices[0].message.content.strip()
        print(f"Active Mode - OpenAI response received: {ai_response[:50]}...")
        return ai_response
        
    except Exception as e:
        print(f"OpenAI API Error in active mode: {e}")
        import traceback
        traceback.print_exc()
        return "I'm having some connection issues right now, but I'm still here with you. What's going on?"
