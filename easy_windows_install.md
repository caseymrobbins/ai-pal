## Windows Desktop App (Easy Install)

This method uses a PowerShell script to install all dependencies (Git, Docker Desktop, Python) and create a simple desktop application to launch AI-Pal.

### Installation

1.  Open Windows PowerShell **as Administrator**.
2.  You may need to allow scripts to run in your current session. You can do this by typing the following command and pressing Enter:
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    ```
3.  Navigate to the directory where you downloaded the `Install_AI_Pal_App.ps1` script. For example:
    ```powershell
    cd C:\Users\YourUser\Downloads
    ```
4.  Run the installer script:
    ```powershell
    .\Install_AI_Pal_App.ps1
    ```
5.  Press **Enter** to continue when prompted.
6.  You **must** approve all User Account Control (UAC) prompts that appear for installing Git, Docker, and Python.
7.  The script will pause to refresh your system's path after installing the prerequisites.
8.  When prompted, enter your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. You can press Enter to skip either key if you don't have one.
9.  The script will automatically clone the repository, set up the configuration file, and create a new "AI-Pal" shortcut on your desktop.
10. **CRITICAL:** Once the script shows "Part 1 Complete! REBOOT REQUIRED", you **must reboot your computer** for the Docker installation to finalize.

### How to Start AI-Pal

1.  After your computer has rebooted, double-click the new **"AI-Pal"** icon on your desktop.
2.  A small application window will open. Click the **"Start AI-Pal"** button inside this window.
3.  The app will automatically start Docker Desktop in the background (if it's not already running) and wait for it to be ready. It will then build and launch the AI-Pal containers.
4.  Once the server is running, the window will automatically load the AI-Pal interface (http://localhost:8000).
5.  To stop the application, you can either click the **"Stop AI-Pal"** button in the app window or simply close the window, which will also shut down the containers.
