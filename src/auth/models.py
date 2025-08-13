from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password, bcrypt_instance):
        """Hashes and stores the password."""
        self.password_hash = bcrypt_instance.generate_password_hash(password).decode('utf-8')

    def check_password(self, password, bcrypt_instance):
        """Checks the password against the stored hash."""
        return bcrypt_instance.check_password_hash(self.password_hash, password)
