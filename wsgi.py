# wsgi.py in your project root
from app import flask_app as application

# This is the object that Gunicorn will use
app = application

if __name__ == "__main__":
    app.run()