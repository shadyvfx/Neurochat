import os
from flask import Flask, render_template, session, jsonify, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, current_user
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
        # Check if user is already authenticated
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        # Always start fresh guest session when server loads
        session['guest_start_time'] = time.time()
        session['guest_mode'] = 'guest'
        session['conversation_history'] = []
        session['guest_expired_notified'] = False
        
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
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
