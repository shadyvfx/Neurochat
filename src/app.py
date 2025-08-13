import os
from flask import Flask, render_template, session, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from decouple import config as env_config
from config import config_dict
import time

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or env_config('FLASK_ENV', default='development')
    app.config.from_object(config_dict.get(config_name, config_dict['default']))
    
    # Initialize extensions
    from auth.models import db
    db.init_app(app)
    migrate = Migrate(app, db)
    bcrypt = Bcrypt(app)
    app.extensions['bcrypt'] = bcrypt  # Store bcrypt in extensions
    csrf = CSRFProtect(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    from auth import auth
    app.register_blueprint(auth, url_prefix='/auth')
    
    @login_manager.user_loader
    def load_user(user_id):
        from auth.models import User
        return User.query.get(int(user_id))
    
    # Main routes
    @app.route('/')
    def index():
        # Always start fresh guest session when server loads
        session['guest_start_time'] = time.time()
        session['guest_mode'] = 'guest'
        session['conversation_history'] = []
        session['guest_expired_notified'] = False
        
        # Check if guest time has expired (15 minutes = 900 seconds)
        guest_elapsed = time.time() - session.get('guest_start_time', 0)
        if guest_elapsed > 900:  # 15 minutes
            session['guest_expired'] = True
            return render_template('index.html', guest_expired=True)
        
        return render_template('index.html', guest_expired=False)
    
    @app.route('/guest/status', methods=['GET'])
    def guest_status():
        """Get guest session status and remaining time"""
        if 'guest_start_time' not in session:
            return jsonify({"error": "No guest session"}), 400
        
        current_time = time.time()
        elapsed = current_time - session.get('guest_start_time', 0)
        remaining = max(0, 900 - elapsed)  # 15 minutes = 900 seconds
        
        # Check if expired
        if remaining <= 0 and not session.get('guest_expired_notified', False):
            # Add expiration message to chat history
            if 'conversation_history' in session:
                session['conversation_history'].append({
                    'role': 'ai',
                    'content': 'Your 15-minute guest session has expired. Please create a free account to continue chatting.',
                    'timestamp': current_time
                })
            session['guest_expired_notified'] = True
        
        return jsonify({
            "guest_mode": session.get('guest_mode', False),
            "remaining_time": remaining,
            "expired": remaining <= 0,
            "expired_notified": session.get('guest_expired_notified', False)
        })
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard route accessible after login/signup"""
        return render_template('dashboard.html')
    
    return app

# Create app instance
app = create_app()

# Initialize database after app creation
with app.app_context():
    try:
        print("Starting database initialization...")
        
        # Use the configured instance path from config
        instance_path = app.config.get('INSTANCE_DIR', os.path.join(os.getcwd(), 'instance'))
        print(f"Instance path: {instance_path}")
        
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
            print(f"Created instance directory: {instance_path}")
        else:
            print(f"Instance directory already exists: {instance_path}")
        
        print("Importing database models...")
        from auth.models import db, User
        print("Database models imported successfully")
        
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully")
        
        # Check if we have any users
        user_count = User.query.count()
        print(f"Current user count: {user_count}")
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Database initialization error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        print("Database initialization failed!")

if __name__ == '__main__':
    app.run(debug=env_config('DEBUG', default=False, cast=bool), 
            host='0.0.0.0', 
            port=int(env_config('PORT', default=5000)))
