#!/bin/bash
# --- AI-Pal Full Desktop App Installer for macOS ---
# This script installs Homebrew, Git, Docker, Python, and PyWebview,
# clones the repo, prompts for keys, and creates a
# self-contained macOS App wrapper that auto-starts Docker.

echo -e "\033[0;32m--- Starting AI-Pal Desktop App Setup for macOS ---\033[0m"

# --- Step 1: Check for/Install Homebrew ---
if ! command -v brew &> /dev/null; then
    echo -e "\033[0;33m[Step 1/7] Homebrew (package manager) not found.\033[0m"
    echo "This script will attempt to install it. It may ask for your password."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    if [ $? -ne 0 ]; then
        echo -e "\033[0;31mError: Homebrew installation failed. Please install it manually from https://brew.sh/ and run this script again.\033[0m"
        exit 1
    fi
    # Add brew to PATH for this script's session
    echo "Adding Homebrew to your PATH..."
    (echo; echo 'eval "$(/opt/homebrew/bin/brew shellenv)"') >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo -e "\033[0;32m[Step 1/7] Homebrew is already installed.\033[0m"
fi

# --- Step 2: Install Prerequisites ---
echo "[Step 2/7] Checking Git installation..."
if command -v git &> /dev/null; then
    echo -e "\033[0;32mGit is already installed. Skipping...\033[0m"
else
    echo "Installing Git..."
    brew install git
    if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to install Git.\033[0m"; exit 1; fi
fi

echo "[Step 3/7] Checking Docker Desktop installation..."
if command -v docker &> /dev/null; then
    echo -e "\033[0;32mDocker Desktop is already installed. Skipping...\033[0m"
else
    echo "Installing Docker Desktop..."
    brew install --cask docker
    if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to install Docker Desktop.\033[0m"; exit 1; fi
fi

echo "[Step 4/7] Checking Python 3.9 installation..."
if command -v python3.9 &> /dev/null; then
    pythonVersion=$(python3.9 --version 2>&1)
    echo -e "\033[0;32mPython 3.9 is already installed ($pythonVersion). Skipping...\033[0m"
else
    echo "Installing Python 3.9..."
    brew install python@3.9
    if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to install Python.\033[0m"; exit 1; fi
fi

# Ensure Homebrew's Python is first in PATH
export PATH="/opt/homebrew/opt/python@3.9/bin:$PATH"

# --- Step 5: Install Python Libraries for Wrapper ---
echo "[Step 5/7] Installing PyWebview and Docker libraries..."
python3.9 -m pip install pywebview "docker>=6.0.0" "psutil>=5.0.0"
if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to install Python libraries.\033[0m"; exit 1; fi

# --- Step 6: Clone Repo and Configure .env ---
repoUrl="https://github.com/caseymrobbins/ai-pal.git"
projectDir="ai-pal"
installBaseDir=$(pwd)
projectFullPath="$installBaseDir/$projectDir"

echo "[Step 6/7] Cloning 'ai-pal' repository into '$projectFullPath'..."
git clone "$repoUrl" "$projectFullPath"
if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to clone repository.\033[0m"; exit 1; fi

echo "Configuring API Keys..."
envFile="$projectFullPath/.env"
exampleFile="$projectFullPath/.env.example"

echo -n "Enter your OPENAI_API_KEY (press Enter to skip): "
read openaiKey
echo -n "Enter your ANTHROPIC_API_KEY (press Enter to skip): "
read anthropicKey

cp "$exampleFile" "$envFile"
if [ $? -ne 0 ]; then echo -e "\033[0;31mError: Failed to create .env file.\033[0m"; exit 1; fi

if [[ -n "$openaiKey" ]]; then
    sed -i '' "s|OPENAI_API_KEY=your_key_here|OPENAI_API_KEY=$openaiKey|g" "$envFile"
fi
if [[ -n "$anthropicKey" ]]; then
    sed -i '' "s|ANTHROPIC_API_KEY=your_key_here|ANTHROPIC_API_KEY=$anthropicKey|g" "$envFile"
fi
echo -e "\033[0;32m.env file configured.\033[0m"

# --- Step 7: Create the Python Wrapper App and macOS .app ---
echo "[Step 7/7] Creating Python GUI App and Desktop .app..."
appPath="$installBaseDir/run_ai_pal_app.py"
desktopAppPath="$HOME/Desktop/AI-Pal.app"
pythonCmdPath="/opt/homebrew/opt/python@3.9/bin/python3.9"

# Create the Python Wrapper App
# Note: DOCKER_PROC_NAME is 'Docker' on Mac
# Note: Must use 'open /Applications/Docker.app' to launch
# Note: Must remove 'creationflags' from subprocess calls
# Note: Must add /usr/local/bin to PATH for docker-compose
cat << EOF > "$appPath"
import webview
import docker
import threading
import time
import os
import sys
import subprocess
import psutil

# --- Configuration ---
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
    
AI_PAL_DIR = os.path.join(BASE_DIR, 'ai-pal')
AI_PAL_URL = 'http://localhost:8000'
DOCKER_APP_PATH = r'/Applications/Docker.app'
DOCKER_PROC_NAME = 'Docker' # Main process name on macOS

# HTML for the loading/control screen
HTML_CONTROLS = '''
<html>
<head>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; color: #333; margin: 0; }
        h1 { font-weight: 300; }
        button { font-size: 16px; padding: 12px 24px; border: none; border-radius: 6px; cursor: pointer; background: #007aff; color: white; margin: 10px; min-width: 150px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #999; cursor: not-allowed; }
        #status { margin-top: 20px; font-size: 14px; color: #555; }
    </style>
</head>
<body>
    <h1>Welcome to AI-Pal</h1>
    <div id="controls">
        <button id="btnStart" onclick="pywebview.api.start_server()">Start AI-Pal</button>
        <button id="btnStop" onclick="pywebview.api.stop_server()">Stop AI-Pal</button>
    </div>
    <div id="status">Status: Idle</div>
    <script>
        function updateStatus(message) {
            document.getElementById('status').innerText = 'Status: ' + message;
        }
        function setControls(disabled) {
            document.getElementById('btnStart').disabled = disabled;
            document.getElementById('btnStop').disabled = disabled;
        }
    </script>
</body>
</html>
'''

class Api:
    def __init__(self):
        self._window = None
        self.docker_client = None
        self.compose_process = None
        # Ensure docker-compose (from Homebrew) is in the PATH
        self.env = os.environ.copy()
        self.env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + self.env.get("PATH", "")

    def set_window(self, window):
        self._window = window

    def _update_status(self, message):
        print(message)
        self._window.evaluate_js(f'updateStatus("{message}")')
        
    def _set_controls(self, disabled):
        self._window.evaluate_js(f'setControls({str(disabled).lower()})')

    def _check_and_start_docker(self):
        self._update_status("Checking Docker status...")
        
        # 1. Check if Docker Desktop process is running
        docker_running = DOCKER_PROC_NAME in (p.name() for p in psutil.process_iter())
        
        if not docker_running:
            self._update_status("Starting Docker Desktop... Please wait.")
            try:
                # Use 'open' command on macOS
                subprocess.Popen(['open', DOCKER_APP_PATH])
            except FileNotFoundError:
                self._update_status(f"Error: Docker not found at {DOCKER_APP_PATH}")
                return False
            except Exception as e:
                self._update_status(f"Error starting Docker: {str(e)}")
                return False
        
        # 2. Wait for Docker Daemon (Engine) to be ready
        self._update_status("Waiting for Docker engine to respond...")
        retries = 60 # Wait up to 2 minutes (60 * 2 seconds)
        for i in range(retries):
            try:
                if not self.docker_client:
                    self.docker_client = docker.from_env(timeout=5)
                self.docker_client.ping()
                self._update_status("Docker engine is ready.")
                return True
            except Exception as e:
                print(f"Waiting for Docker daemon... ({i+1}/{retries})")
                time.sleep(2)
        
        self._update_status("Error: Docker engine failed to start.")
        return False

    def start_server(self):
        def _run():
            self._set_controls(True) # Disable buttons
            
            # Step 1: Ensure Docker is running
            if not self._check_and_start_docker():
                self._set_controls(False) # Re-enable buttons
                return # Stop if Docker failed
            
            # Step 2: Start docker-compose
            try:
                self._update_status("Starting AI-Pal containers... (This may take a minute)")
                self.compose_process = subprocess.Popen(
                    ['docker-compose', 'up', '--build'],
                    cwd=AI_PAL_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=self.env # Pass the modified env
                )
                
                self._update_status("Waiting for AI-Pal server (http://localhost:8000)...")
                
                # Step 3: Wait for the web server to be accessible
                import urllib.request
                retries = 30
                for i in range(retries):
                    try:
                        if urllib.request.urlopen(AI_PAL_URL, timeout=2).getcode() == 200:
                            self._update_status("AI-Pal is running.")
                            self._window.load_url(AI_PAL_URL)
                            self._set_controls(False)
                            return
                    except Exception:
                        print(f"Waiting for AI-Pal web server... ({i+1}/{retries})")
                        time.sleep(2)
                
                self._update_status("Error: AI-Pal server failed to start.")
                self.stop_server() # Stop if it failed
                
            except Exception as e:
                self._update_status(f"Error: {str(e).replace('"', '`')}")
            
            self._set_controls(False) # Re-enable buttons on failure

        threading.Thread(target=_run, daemon=True).start()

    def stop_server(self):
        def _run():
            self._set_controls(True)
            self._update_status("Stopping AI-Pal containers...")
            try:
                # Terminate our own compose process if it's running
                if self.compose_process and self.compose_process.poll() is None:
                    self.compose_process.terminate()
                
                # Run docker-compose down to clean up
                subprocess.run(
                    ['docker-compose', 'down'],
                    cwd=AI_PAL_DIR,
                    check=True,
                    env=self.env
                )
                self._update_status("AI-Pal stopped.")
                self._window.load_html(HTML_CONTROLS)
            except Exception as e:
                self._update_status(f"Error stopping: {str(e).replace('"', '`')}")
            
            self._set_controls(False)
        
        threading.Thread(target=_run, daemon=True).start()

def on_closing():
    print("Window closed, stopping containers...")
    env = os.environ.copy()
    env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + env.get("PATH", "")
    try:
        subprocess.run(
            ['docker-compose', 'down'],
            cwd=AI_PAL_DIR,
            check=False,
            env=env
        )
        print("Containers stopped.")
    except Exception as e:
        print(f"Error on closing: {e}")

if __name__ == '__main__':
    api = Api()
    window = webview.create_window(
        'AI-Pal',
        html=HTML_CONTROLS,
        js_api=api,
        width=1280,
        height=800
    )
    api.set_window(window)
    window.events.closing += on_closing
    webview.start(debug=False)
EOF

# Create the .app wrapper using AppleScript
# This creates a double-clickable application on the Desktop
# It runs the python script in the background
echo "Creating macOS Application on your Desktop..."
if [ -d "$desktopAppPath" ]; then
    rm -r "$desktopAppPath"
fi

osacompile -o "$desktopAppPath" -e "do shell script \"$pythonCmdPath $appPath > /dev/null 2>&1 &\""

if [ $? -ne 0 ]; then
    echo -e "\033[0;33mWarning: Could not create desktop .app. \033[0m"
    echo "You can still run AI-Pal by running this command in your terminal:"
    echo "python3.9 $appPath"
else
    echo -e "\033[0;32mDesktop app 'AI-Pal.app' created.\033[0m"
fi

# --- Final Instructions ---
echo -e "\033[0;36m--------------------------------------------------------\033[0m"
echo -e "\033[0;36m--- 🚀 Installation Complete! ---
\033[0m"
echo -e "\033[0;32mThe automated installation is done. (No reboot is required for Mac).\033[0m"
echo ""
echo "1. Double-click the new 'AI-Pal' app on your desktop."
echo "   (You DO NOT need to start Docker manually)."
echo ""
echo "2. The app will open. Click 'Start AI-Pal' inside it."
echo "   It will automatically launch Docker Desktop if needed,"
echo "   wait for it to be ready, and then start the AI-Pal server."
echo -e "\033[0;36m--------------------------------------------------------\033[0m"
echo "Press Enter to exit"
read
