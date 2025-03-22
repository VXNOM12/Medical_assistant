import sys
print(f"WSGI initializing with Python {sys.version}")

from app import app

if __name__ == "__main__":
    app.run()