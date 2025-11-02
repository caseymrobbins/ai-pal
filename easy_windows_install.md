Windows Desktop App (Easy Install)
This method uses a PowerShell script to install all dependencies (Git, Docker Desktop, Python) and create a simple desktop application to launch AI-Pal.

Installation
Open Windows PowerShell as Administrator.

You may need to allow scripts to run in your current session. You can do this by typing the following command and pressing Enter:

PowerShell

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
Navigate to the directory where you downloaded the Install_AI_Pal_App.ps1 script. For example:

PowerShell

cd C:\Users\YourUser\Downloads
Run the installer script:

PowerShell

.\Install_AI_Pal_App.ps1
Press Enter to continue when prompted.

You must approve all User Account Control (UAC) prompts that appear for installing Git, Docker, and Python.

The script will pause to refresh your system's path after installing the prerequisites.

When prompted, enter your OPENAI_API_KEY and ANTHROPIC_API_KEY. You can press Enter to skip either key if you don't have one.

The script will automatically clone the repository, set up the configuration file, and create a new "AI-Pal" shortcut on your desktop.

CRITICAL: Once the script shows "Part 1 Complete! REBOOT REQUIRED", you must reboot your computer for the Docker installation to finalize.

How to Start AI-Pal
After your computer has rebooted, double-click the new "AI-Pal" icon on your desktop.

A small application window will open. Click the "Start AI-Pal" button inside this window.

The app will automatically start Docker Desktop in the background (if it's not already running) and wait for it to be ready. It will then build and launch the AI-Pal containers.

Once the server is running, the window will automatically load the AI-Pal interface (http://localhost:8000).

To stop the application, you can either click the "Stop AI-Pal" button in the app window or simply close the window, which will also shut down the containers.
