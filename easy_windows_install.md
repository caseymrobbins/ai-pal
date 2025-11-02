## Windows Desktop App (Easy Install)

This method uses a PowerShell script to install all dependencies (Git, Docker Desktop, Python) and create a simple desktop application to launch AI-Pal.

### Installation

1.  **Download the Installer Script:**
    * **[Install_AI_Pal_App.ps1](https://raw.githubusercontent.com/caseymrobbins/ai-pal/refs/heads/main/Install_AI_Pal_App.ps1)**
    * **Important:** Right-click the link and select **"Save as..."** or **"Save link as..."** to download the file. Remember where you save it (e.g., your `Downloads` folder).

2.  **Open PowerShell as Administrator:**
    * Click the Start menu.
    * Type `PowerShell`.
    * Right-click on "Windows PowerShell" and select **"Run as administrator"**.

3.  **Allow the Script to Run (for this session):**
    * In the blue Administrator PowerShell window, copy and paste the following command, then press Enter. This is necessary to get around Windows' default script security policy.
    ```powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    ```

4.  **Navigate to the Script and Run It:**
    * First, change to the directory where you saved the file. For example, if you saved it to your `Downloads` folder:
    ```powershell
    cd $HOME\Downloads
    ```
    * (If you saved it elsewhere, use `cd C:\path\to\your\folder`)
    * Now, run the script by typing its name and pressing Enter:
    ```powershell
    .\Install_AI_Pal_App.ps1
    ```

5.  **Follow the On-Screen Prompts:**
    * Press **Enter** to continue when the script starts.
    * You **must** approve all User Account Control (UAC) prompts that appear for installing Git, Docker, and Python.
    * When prompted, enter your `OPENAI_API_KEY` and `ANTHROPIC_API_KEY`. You can press Enter to skip either key.
    * The script will clone the repository and create a new "AI-Pal" shortcut on your desktop.

6.  **Reboot Your Computer:**
    * **CRITICAL:** Once the script shows "Part 1 Complete! REBOOT REQUIRED", you **must reboot your computer**. This is a one-time step required for the Docker installation to finalize.

### How to Start AI-Pal

1.  After your computer has rebooted, double-click the new **"AI-Pal"** icon on your desktop.
2.  A small application window will open. Click the **"Start AI-Pal"** button inside this window.
3.  The app will automatically start Docker Desktop in the background (if it's not already running) and wait for it to be ready. It will then build and launch the AI-Pal containers.
4.  Once the server is running, the window will automatically load the AI-Pal interface (http://localhost:8000).
5.  To stop the application, you can either click the **"Stop AI-Pal"** button in the app window or simply close the window, which will also shut down the containers.
