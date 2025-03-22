import sys
import os
print(f"WSGI initializing with Python {sys.version}")

try:
    from app import app
    print("Successfully imported Flask application from app.py")
except Exception as e:
    print(f"Error importing Flask application: {e}")
    # Create a minimal emergency application
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def emergency_home():
        return "Emergency mode: Application failed to load properly."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)