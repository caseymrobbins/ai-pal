# --- AI-Pal Full Desktop App Installer (Smart Docker Handling) ---
# This script installs Git, Docker, Python, and PyWebview,
# clones the repo, prompts for keys, and creates a
# self-contained Python GUI wrapper that auto-starts Docker.

Write-Host "--- Starting AI-Pal Desktop App Setup ---" -ForegroundColor Green
Write-Host "This script will install Git, Docker Desktop, and Python 3.9."
Write-Host "You MUST approve any User Account Control (UAC) prompts."
Write-Host "WARNING: Installing Docker Desktop will require a system REBOOT." -ForegroundColor Yellow
Read-Host -Prompt "Press Enter to continue..."

# --- Step 1: Install Prerequisites ---
Write-Host "[Step 1/6] Checking Git installation..."
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-Host "Git is already installed. Skipping..." -ForegroundColor Green
} else {
    Write-Host "Installing Git..."
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { Write-Host "Error: Winget failed to install Git." -ForegroundColor Red; exit 1 }
}

Write-Host "[Step 2/6] Checking Docker Desktop installation..."
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "Docker Desktop is already installed. Skipping..." -ForegroundColor Green
} else {
    Write-Host "Installing Docker Desktop..."
    winget install --id Docker.DockerDesktop -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { Write-Host "Error: Winget failed to install Docker." -ForegroundColor Red; exit 1 }
}

Write-Host "[Step 3/6] Checking Python 3.9 installation..."
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version 2>&1
    Write-Host "Python is already installed ($pythonVersion). Skipping..." -ForegroundColor Green
} else {
    Write-Host "Installing Python 3.9..."
    winget install --id Python.Python.3.9 -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { Write-Host "Error: Winget failed to install Python." -ForegroundColor Red; exit 1 }
}

Write-Host "--- Prerequisites installed. ---"
Write-Host "Pausing for 10 seconds to allow PATH to refresh..."
Start-Sleep -Seconds 10
Write-Host "Refreshing environment path..."
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# --- Step 4: Install Python Libraries for Wrapper ---
Write-Host "[Step 4/6] Installing PyWebview and Docker libraries..."
try {
    $pythonExe = "python.exe"
    & $pythonExe -m pip install pywebview "docker>=6.0.0" "psutil>=5.0.0"
    Write-Host "Python libraries (pywebview, docker, psutil) installed." -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to install Python libraries." -ForegroundColor Red; exit 1
}

# --- Step 5: Clone Repo and Configure .env ---
$repoUrl = "https://github.com/caseymrobbins/ai-pal.git"
$projectDir = "ai-pal"
$installBaseDir = (Get-Location).Path
$projectFullPath = Join-Path -Path $installBaseDir -ChildPath $projectDir

Write-Host "[Step 5/6] Cloning 'ai-pal' repository into '$projectFullPath'..."
try {
    git clone $repoUrl $projectFullPath
    Write-Host "Repository cloned successfully." -ForegroundColor Green
} catch {
    Write-Host "Error: Failed to clone repository." -ForegroundColor Red; exit 1
}

Write-Host "Configuring API Keys..."
$envFile = Join-Path -Path $projectFullPath -ChildPath ".env"
$exampleFile = Join-Path -Path $projectFullPath -ChildPath ".env.example"

$openaiKey = Read-Host -Prompt "Enter your OPENAI_API_KEY (press Enter to skip)"
$anthropicKey = Read-Host -Prompt "Enter your ANTHROPIC_API_KEY (press Enter to skip)"

try {
    Copy-Item -Path $exampleFile -Destination $envFile
    $content = Get-Content $envFile
    if (-not [string]::IsNullOrEmpty($openaiKey)) { $content = $content -replace 'OPENAI_API_KEY=your_key_here', "OPENAI_API_KEY=$openaiKey" }
    if (-not [string]::IsNullOrEmpty($anthropicKey)) { $content = $content -replace 'ANTHROPIC_API_KEY=your_key_here', "ANTHROPIC_API_KEY=$anthropicKey" }
    Set-Content -Path $envFile -Value $content
    Write-Host ".env file configured." -ForegroundColor Green
} catch {
    Write-Host "Error creating .env file." -ForegroundColor Red
}

# --- Step 6: Create the Python Wrapper App and Desktop Shortcut ---
Write-Host "[Step 6/6] Creating Python GUI App and Desktop Shortcut..."
$appPath = Join-Path -Path $installBaseDir -ChildPath "run_ai_pal_app.pyw"

# Create the Python Wrapper App (.pyw hides the console)
$pywContent = @"
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
DOCKER_EXE_PATH = r'C:\Program Files\Docker\Docker\Docker Desktop.exe'
DOCKER_PROC_NAME = 'Docker Desktop.exe'

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
            document.getElementById('status').innerText = 'Status: 'D + message;
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
                subprocess.Popen([DOCKER_EXE_PATH])
            except FileNotFoundError:
                self._update_status(f"Error: Docker not found at {DOCKER_EXE_PATH}")
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
                    creationflags=subprocess.CREATE_NO_WINDOW
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
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self._update_status("AI-Pal stopped.")
                self._window.load_html(HTML_CONTROLS)
            except Exception as e:
                self._update_status(f"Error stopping: {str(e).replace('"', '`')}")
            
            self._set_controls(False)
        
        threading.Thread(target=_run, daemon=True).start()

def on_closing():
    # Attempt a clean shutdown of Docker containers when app window is closed
    print("Window closed, stopping containers...")
    try:
        subprocess.run(
            ['docker-compose', 'down'],
            cwd=AI_PAL_DIR,
            check=False,
            creationflags=subprocess.CREATE_NO_WINDOW
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

"@
Set-Content -Path $appPath -Value $pywContent

# Create the Desktop Shortcut
$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path -Path $desktopPath -ChildPath "AI-Pal.lnk"
$wshell = New-Object -ComObject WScript.Shell
$shortcut = $wshell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "pythonw.exe"
$shortcut.Arguments = """$appPath"""
$shortcut.WorkingDirectory = $installBaseDir
$shortcut.IconLocation = "shell32.dll, 220" # A web/network icon
$shortcut.Description = "Run the AI-Pal Application"
$shortcut.Save()

Write-Host "Desktop app and shortcut created." -ForegroundColor Green

# --- Final Instructions ---
Write-Host "--------------------------------------------------------" -ForegroundColor Cyan
Write-Host "--- 🚀 Part 1 Complete! REBOOT REQUIRED ---" -ForegroundColor Cyan
Write-Host "--------------------------------------------------------" -ForegroundColor Yellow
Write-Host "The automated installation is done. You must now:"
Write-Host ""
Write-Host "1. REBOOT YOUR COMPUTER. This is a one-time step for Docker."
Write-Host ""
Write-Host "2. After rebooting, double-click the new 'AI-Pal' icon on your desktop."
Write-Host "   (You DO NOT need to start Docker manually)."
Write-Host ""
Write-Host "3. The app will open. Click 'Start AI-Pal' inside it."
Write-Host "   It will automatically launch Docker Desktop if needed,"
Write-Host "   wait for it to be ready, and then start the AI-Pal server."
Write-Host "--------------------------------------------------------"
Read-Host -Prompt "Press Enter to exit"
