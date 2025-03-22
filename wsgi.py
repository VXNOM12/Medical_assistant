# wsgi.py
import sys
import os

# Print debugging information
print("=" * 50)
print("WSGI INITIALIZATION")
print("Python version:", sys.version)
print("Working directory:", os.getcwd())
print("Directory contents:", os.listdir('.'))
print("=" * 50)

# Import the Flask app
try:
    from app.flask_app import app
    print("Successfully imported Flask application from flask_app.py")
except Exception as e:
    print(f"Error importing Flask application: {e}")
    # Create a minimal emergency application
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    def emergency_home():
        return "Emergency mode: Flask application failed to load properly."
    
    @app.route('/health')
    def emergency_health():
        return jsonify({"status": "emergency_mode", "error": str(e)})

# This is what Gunicorn will use
if __name__ == "__main__":
    app.run()