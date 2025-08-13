# Flask Authentication App

A production-ready Flask web application with user authentication, featuring signup, login, and dashboard functionality.

## Features

- ✅ User Registration & Authentication
- ✅ Secure Password Hashing
- ✅ Modal-based Login/Signup Forms
- ✅ CSRF Protection
- ✅ Production-Ready Configuration
- ✅ Database Integration
- ✅ Responsive UI

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd flash-basic-auth
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application**
   ```bash
   python src/app.py
   ```

   Visit: http://127.0.0.1:5000

### Production Deployment

#### Heroku

1. **Install Heroku CLI**
2. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY="your-super-secret-key-here"
   heroku config:set FLASK_ENV=production
   heroku config:set DEBUG=False
   ```

4. **Deploy**
   ```bash
   git add .
   git commit -m "Deploy to production"
   git push heroku main
   ```

#### Other Platforms

- **Railway**: Connect your GitHub repo and deploy
- **DigitalOcean**: Use App Platform or Droplets
- **AWS**: Deploy using Elastic Beanstalk or EC2

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key (REQUIRED in production) | `dev_key_change_this_in_production` |
| `FLASK_ENV` | Environment (`development`/`production`) | `development` |
| `DEBUG` | Debug mode (`True`/`False`) | `False` |
| `DATABASE_URL` | Database connection string | `sqlite:///instance/users.db` |
| `PORT` | Port to run the app | `5000` |

## Project Structure

```
flash-basic-auth/
├── src/
│   ├── app.py              # Main application
│   ├── config.py           # Configuration classes
│   ├── auth/
│   │   ├── __init__.py     # Blueprint initialization
│   │   ├── models.py       # User model
│   │   ├── routes.py       # Authentication routes
│   │   └── forms.py        # WTForms (if needed)
│   ├── static/
│   │   ├── css/            # Stylesheets
│   │   └── js/             # JavaScript files
│   ├── templates/          # HTML templates
│   └── instance/           # Database files (local)
├── wsgi.py                 # WSGI entry point
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku process file
├── runtime.txt            # Python version
└── README.md              # This file
```

## Security Features

- 🔒 Password hashing with Werkzeug
- 🛡️ CSRF protection
- 🔐 Secure session management
- 🚫 SQL injection prevention
- ⚠️ Input validation

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **Security**: Flask-WTF, Werkzeug
- **Deployment**: Gunicorn, Heroku-ready

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
"# Neurochat" 
