import os
import sys
import subprocess
import time
import webbrowser
import shutil
from threading import Thread

def check_npm_installed():
    """Check if npm is installed and available in the PATH."""
    npm_path = shutil.which("npm")
    if npm_path:
        return npm_path
    return None

def start_backend():
    """Start the Flask backend server."""
    try:
        os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

        # Ensure the instance directory exists
        instance_dir = os.path.join(os.getcwd(), "instance")
        if not os.path.exists(instance_dir):
            os.makedirs(instance_dir)

        # Check if the default database exists, if not initialize it
        default_db_path = os.path.join(instance_dir, "kegelmanager_de4fault.db")

        if not os.path.exists(default_db_path):
            # We'll let app.py handle the creation of the default database
            pass

        # Start the Flask server
        subprocess.run([sys.executable, "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting backend: {e}")
    except Exception as e:
        print(f"Unexpected error starting backend: {e}")

def start_frontend(npm_path="npm"):
    """Start the React frontend development server."""
    try:
        os.chdir(os.path.join(os.path.dirname(__file__), "frontend"))

        # Install dependencies if node_modules doesn't exist
        if not os.path.exists("node_modules"):
            subprocess.run([npm_path, "install"], check=True)

        # Start the development server
        subprocess.run([npm_path, "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting frontend: {e}")
    except Exception as e:
        print(f"Unexpected error starting frontend: {e}")

def main():
    """Main function to start both servers."""
    # Check if npm is installed
    npm_path = check_npm_installed()
    if not npm_path:
        print("\nERROR: npm not found. Please install Node.js and npm.")
        print("You can download Node.js from https://nodejs.org/")
        print("\nAlternatively, you can run the backend only:")
        print("1. Navigate to the 'kegelmanager/backend' directory")
        print("2. Run 'python init_db.py --sample' to initialize the database")
        print("3. Run 'python app.py' to start the Flask server")
        return

    # Get the current directory
    current_dir = os.getcwd()

    # Start the backend in a separate thread
    backend_thread = Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()

    # Give the backend some time to start
    time.sleep(3)

    # Change back to the original directory
    os.chdir(current_dir)

    # Open the browser to the main menu
    webbrowser.open("http://localhost:5173/main-menu")

    # Start the frontend
    start_frontend(npm_path)

if __name__ == "__main__":
    main()
