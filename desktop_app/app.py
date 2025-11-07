"""
AI-Pal Desktop Application Wrapper

A cross-platform desktop application for managing AI-Pal services.
Provides Docker control, status monitoring, and diagnostics.

Platform Support: macOS, Windows
Dependencies: pywebview, docker, psutil
"""

import webview
import docker
import threading
import time
import os
import sys
import subprocess
import psutil
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# Logging Configuration
# ============================================================================

# Setup logging
LOG_DIR = Path.home() / '.ai-pal' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f'desktop_app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration & Constants
# ============================================================================

class Platform(Enum):
    """Supported platforms"""
    MACOS = "darwin"
    WINDOWS = "win32"
    LINUX = "linux"

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ServiceInfo:
    """Service status information"""
    name: str
    status: ServiceStatus
    last_check: str
    port: Optional[int] = None
    url: Optional[str] = None
    status_history: List[tuple] = None  # List of (timestamp, status) tuples

    def __post_init__(self):
        """Initialize status history if not provided"""
        if self.status_history is None:
            self.status_history = [(self.last_check, self.status)]

    def add_status_update(self, status: ServiceStatus, timestamp: str) -> None:
        """Add status update to history"""
        self.status_history.append((timestamp, status))
        # Keep only last 20 status updates
        if len(self.status_history) > 20:
            self.status_history = self.status_history[-20:]
        self.status = status
        self.last_check = timestamp

@dataclass
class ErrorInfo:
    """Error information with recovery suggestions"""
    message: str
    severity: ErrorSeverity
    code: str
    timestamp: str
    suggestions: List[str]
    details: Optional[str] = None

@dataclass
class AppNotification:
    """Notification to display to user"""
    title: str
    message: str
    notification_type: str  # 'success', 'error', 'info', 'warning'
    timestamp: str

# Platform Detection
PLATFORM = sys.platform
IS_MACOS = PLATFORM == Platform.MACOS.value
IS_WINDOWS = PLATFORM == Platform.WINDOWS.value

# Docker Configuration
DOCKER_APP_PATH = "/Applications/Docker.app" if IS_MACOS else r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
DOCKER_PROC_NAME = "Docker" if IS_MACOS else "Docker Desktop.exe"

# AI-Pal Configuration
AI_PAL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ai-pal')
AI_PAL_URL = 'http://localhost:8000'
API_PORT = 8000

# Services Definition
SERVICES = {
    'api': {'name': 'API Server', 'port': 8000, 'url': 'http://localhost:8000/health'},
    'postgres': {'name': 'PostgreSQL', 'port': 5432},
    'redis': {'name': 'Redis Cache', 'port': 6379},
    'nginx': {'name': 'Nginx', 'port': 80},
    'prometheus': {'name': 'Prometheus', 'port': 9090},
    'grafana': {'name': 'Grafana', 'port': 3000},
}

# ============================================================================
# API Class - Main Application Logic
# ============================================================================

class DesktopAppAPI:
    """Main API for desktop application control"""

    def __init__(self):
        self._window: Optional[webview.api.WebView] = None
        self.docker_client: Optional[docker.DockerClient] = None
        self.compose_process: Optional[subprocess.Popen] = None
        self.operation_lock = threading.Lock()
        self.notifications: List[AppNotification] = []
        self.services: Dict[str, ServiceInfo] = {
            k: ServiceInfo(name=v['name'], status=ServiceStatus.UNKNOWN, last_check="Never")
            for k, v in SERVICES.items()
        }
        self.error_history: List[ErrorInfo] = []

        # Environment setup
        self.env = os.environ.copy()
        if IS_MACOS:
            self.env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + self.env.get("PATH", "")

        logger.info(f"Desktop App initialized. Platform: {PLATFORM}")

    def set_window(self, window: webview.api.WebView) -> None:
        """Set the main window reference"""
        self._window = window

    # ========================================================================
    # Status & Notification Methods
    # ========================================================================

    def _update_status(self, message: str, status_type: str = "info", show_spinner: bool = False) -> None:
        """Update status display in UI"""
        if self._window:
            try:
                # Escape special characters for JavaScript
                safe_message = message.replace('"', '\\"').replace('\n', '\\n')
                self._window.evaluate_js(
                    f'updateStatus("{safe_message}", "{status_type}", {str(show_spinner).lower()})'
                )
            except Exception as e:
                logger.error(f"Failed to update UI status: {e}")
        logger.info(f"[{status_type.upper()}] {message}")

    def _add_notification(self, title: str, message: str, notif_type: str) -> None:
        """Add notification to queue with deduplication"""
        notification = AppNotification(
            title=title,
            message=message,
            notification_type=notif_type,
            timestamp=datetime.now().isoformat()
        )

        # Prevent duplicate notifications (same title and message within 5 seconds)
        recent_notifs = [
            n for n in self.notifications
            if n.title == title and n.message == message
        ]
        if recent_notifs:
            # Check if the most recent one is less than 5 seconds old
            last_notif = recent_notifs[-1]
            last_time = datetime.fromisoformat(last_notif.timestamp)
            if (datetime.now() - last_time).total_seconds() < 5:
                logger.debug(f"Skipped duplicate notification: {title}")
                return

        self.notifications.append(notification)

        # Keep only last 20 notifications in memory
        if len(self.notifications) > 20:
            self.notifications = self.notifications[-20:]

        self._update_ui_notifications()
        logger.info(f"Notification: {title} - {message}")

    def _add_error(self, message: str, severity: ErrorSeverity, code: str,
                   suggestions: List[str], details: Optional[str] = None) -> None:
        """Add error to history with recovery suggestions"""
        error = ErrorInfo(
            message=message,
            severity=severity,
            code=code,
            timestamp=datetime.now().isoformat(),
            suggestions=suggestions,
            details=details
        )

        # Prevent duplicate errors (same code within 10 seconds)
        recent_errors = [
            e for e in self.error_history
            if e.code == code
        ]
        if recent_errors:
            last_error = recent_errors[-1]
            last_time = datetime.fromisoformat(last_error.timestamp)
            if (datetime.now() - last_time).total_seconds() < 10:
                logger.debug(f"Skipped duplicate error: {code}")
                return

        self.error_history.append(error)

        # Keep only last 25 errors in memory
        if len(self.error_history) > 25:
            self.error_history = self.error_history[-25:]

        self._update_ui_errors()
        self._add_notification("Error", message, "error")
        logger.error(f"[{code}] {message}\nDetails: {details}\nSuggestions: {suggestions}")

    def _set_controls(self, disabled: bool) -> None:
        """Enable/disable control buttons"""
        if self._window:
            try:
                self._window.evaluate_js(f'setControls({str(disabled).lower()})')
            except Exception as e:
                logger.error(f"Failed to set controls: {e}")

    def _update_ui_notifications(self) -> None:
        """Update notifications in UI"""
        if self._window:
            try:
                notifs = [asdict(n) for n in self.notifications[-10:]]  # Last 10
                self._window.evaluate_js(f'updateNotifications({json.dumps(notifs)})')
            except Exception as e:
                logger.error(f"Failed to update notifications UI: {e}")

    def _update_ui_errors(self) -> None:
        """Update error history in UI"""
        if self._window:
            try:
                errors = []
                for err in self.error_history[-10:]:  # Last 10
                    err_dict = asdict(err)
                    # Convert ErrorSeverity enum to string value
                    if isinstance(err_dict['severity'], ErrorSeverity):
                        err_dict['severity'] = err_dict['severity'].value
                    errors.append(err_dict)
                self._window.evaluate_js(f'updateErrors({json.dumps(errors)})')
            except Exception as e:
                logger.error(f"Failed to update errors UI: {e}")

    def _update_ui_services(self) -> None:
        """Update service status in UI"""
        if self._window:
            try:
                services_data = {}
                for k, v in self.services.items():
                    svc_dict = asdict(v)
                    # Convert ServiceStatus enum to string value
                    if isinstance(svc_dict['status'], ServiceStatus):
                        svc_dict['status'] = svc_dict['status'].value

                    # Convert status_history tuples to serializable format
                    if 'status_history' in svc_dict and svc_dict['status_history']:
                        svc_dict['status_history'] = [
                            {
                                'timestamp': ts,
                                'status': st.value if isinstance(st, ServiceStatus) else st
                            }
                            for ts, st in svc_dict['status_history']
                        ]
                    else:
                        svc_dict['status_history'] = []

                    services_data[k] = svc_dict
                self._window.evaluate_js(f'updateServices({json.dumps(services_data)})')
            except Exception as e:
                logger.error(f"Failed to update services UI: {e}")

    # ========================================================================
    # Docker Control Methods
    # ========================================================================

    def _check_and_start_docker(self) -> bool:
        """Check Docker status and start if needed"""
        self._update_status("Checking Docker status...", "info")

        # 1. Check if Docker process is running
        docker_running = DOCKER_PROC_NAME in (p.name() for p in psutil.process_iter())

        if not docker_running:
            self._update_status("Docker not running. Starting Docker Desktop...", "info")
            self._add_notification("Docker", "Starting Docker Desktop...", "info")

            try:
                if IS_MACOS:
                    subprocess.Popen(['open', DOCKER_APP_PATH])
                elif IS_WINDOWS:
                    subprocess.Popen([DOCKER_APP_PATH])
                else:
                    self._add_error(
                        "Docker startup not supported on this platform",
                        ErrorSeverity.CRITICAL,
                        "DOCKER_UNSUPPORTED",
                        ["Switch to macOS or Windows", "Start Docker manually"]
                    )
                    return False
            except FileNotFoundError:
                self._add_error(
                    f"Docker not found at {DOCKER_APP_PATH}",
                    ErrorSeverity.CRITICAL,
                    "DOCKER_NOT_FOUND",
                    [
                        "Install Docker Desktop from https://www.docker.com/products/docker-desktop",
                        "Verify installation path is correct",
                        "Restart the application after installation"
                    ],
                    f"Expected Docker at: {DOCKER_APP_PATH}"
                )
                return False
            except Exception as e:
                self._add_error(
                    "Failed to start Docker",
                    ErrorSeverity.CRITICAL,
                    "DOCKER_START_FAILED",
                    ["Restart Docker manually", "Check Docker Desktop logs", "Restart your computer"],
                    str(e)
                )
                return False

        # 2. Wait for Docker daemon to be ready
        self._update_status("Waiting for Docker engine to respond...", "info")
        retries = 60
        for i in range(retries):
            try:
                if not self.docker_client:
                    self.docker_client = docker.from_env(timeout=5)
                self.docker_client.ping()
                self._update_status("Docker engine is ready", "success")
                self._add_notification("Docker", "Docker engine is ready", "success")
                return True
            except Exception:
                progress = f"Waiting for Docker... ({i+1}/{retries})"
                if i % 10 == 0:  # Update every 10 iterations
                    self._update_status(progress, "info")
                time.sleep(2)

        self._add_error(
            "Docker engine failed to start after 2 minutes",
            ErrorSeverity.CRITICAL,
            "DOCKER_TIMEOUT",
            [
                "Check system resources (RAM, CPU)",
                "Check available disk space",
                "Restart Docker Desktop",
                "Restart your computer"
            ],
            "Docker daemon did not respond after 120 seconds"
        )
        return False

    # ========================================================================
    # Server Management Methods
    # ========================================================================

    def start_server(self) -> None:
        """Start AI-Pal server"""
        def _run() -> None:
            self._set_controls(True)
            self._add_notification("Startup", "Starting AI-Pal...", "info")

            try:
                # Step 1: Ensure Docker is running
                self._update_status("Checking Docker...", "info", show_spinner=True)
                if not self._check_and_start_docker():
                    self._set_controls(False)
                    return

                # Step 2: Start docker-compose
                self._update_status("Starting AI-Pal containers...", "info", show_spinner=True)
                self.compose_process = subprocess.Popen(
                    ['docker-compose', 'up', '--build'],
                    cwd=AI_PAL_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=self.env
                )

                # Step 3: Wait for services to be healthy
                self._update_status("Waiting for services to start...", "info", show_spinner=True)
                self._check_services(timeout=120)

                # Step 4: Verify API is responding
                self._update_status("Verifying AI-Pal API...", "info", show_spinner=True)
                if self._verify_api_ready():
                    self._update_status("AI-Pal is running!", "success", show_spinner=False)
                    self._add_notification("Startup", "AI-Pal is ready!", "success")

                    if self._window:
                        self._window.load_url(AI_PAL_URL)

                    self._set_controls(False)
                    return

                self._add_error(
                    "AI-Pal server failed to start",
                    ErrorSeverity.WARNING,
                    "API_FAILED",
                    [
                        "Check docker-compose logs for errors",
                        "Verify all services started successfully",
                        "Check port availability (port 8000)",
                        "Try stopping and restarting"
                    ]
                )
                self.stop_server()

            except FileNotFoundError:
                self._add_error(
                    "docker-compose command not found",
                    ErrorSeverity.CRITICAL,
                    "DOCKER_COMPOSE_NOT_FOUND",
                    [
                        "Ensure Docker Desktop is installed",
                        "Verify docker-compose is in PATH",
                        "Restart the application"
                    ]
                )
            except Exception as e:
                self._add_error(
                    f"Failed to start AI-Pal: {str(e)}",
                    ErrorSeverity.CRITICAL,
                    "STARTUP_FAILED",
                    [
                        "Check the logs below for more details",
                        "Verify Docker Desktop is running",
                        "Check available disk space",
                        "Try restarting Docker"
                    ],
                    str(e)
                )
            finally:
                self._set_controls(False)

        threading.Thread(target=_run, daemon=True).start()

    def stop_server(self) -> None:
        """Stop AI-Pal server"""
        def _run() -> None:
            self._set_controls(True)
            self._add_notification("Shutdown", "Stopping AI-Pal...", "info")
            self._update_status("Stopping AI-Pal containers...", "info")

            try:
                if self.compose_process and self.compose_process.poll() is None:
                    self.compose_process.terminate()
                    try:
                        self.compose_process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        self.compose_process.kill()

                subprocess.run(
                    ['docker-compose', 'down'],
                    cwd=AI_PAL_DIR,
                    check=False,
                    env=self.env,
                    timeout=30
                )

                self._update_status("AI-Pal stopped", "info")
                self._add_notification("Shutdown", "AI-Pal stopped", "success")

                if self._window:
                    self._window.load_html(get_html_controls())

            except subprocess.TimeoutExpired:
                self._add_error(
                    "Timeout stopping containers",
                    ErrorSeverity.WARNING,
                    "STOP_TIMEOUT",
                    ["Force stop using Docker Desktop", "Check running containers"]
                )
            except Exception as e:
                self._add_error(
                    f"Error stopping AI-Pal: {str(e)}",
                    ErrorSeverity.WARNING,
                    "STOP_ERROR",
                    ["Try stopping using Docker Desktop", "Check logs for details"],
                    str(e)
                )
            finally:
                self._set_controls(False)

        threading.Thread(target=_run, daemon=True).start()

    # ========================================================================
    # Service Monitoring Methods
    # ========================================================================

    def _check_services(self, timeout: int = 120) -> None:
        """Check status of all services"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            all_healthy = True

            for service_id, service_info in SERVICES.items():
                port = service_info.get('port')
                url = service_info.get('url')

                # Try to connect to service port
                if port:
                    try:
                        sock = __import__('socket').socket()
                        sock.settimeout(2)
                        result = sock.connect_ex(('localhost', port))
                        sock.close()

                        if result == 0:
                            self.services[service_id].status = ServiceStatus.HEALTHY
                            self.services[service_id].last_check = datetime.now().isoformat()
                        else:
                            all_healthy = False
                            self.services[service_id].status = ServiceStatus.UNHEALTHY
                    except Exception:
                        all_healthy = False
                        self.services[service_id].status = ServiceStatus.UNHEALTHY

                self._update_ui_services()

            if all_healthy:
                return

            time.sleep(2)

    def _verify_api_ready(self, retries: int = 30) -> bool:
        """Verify that AI-Pal API is responding"""
        import urllib.request

        for i in range(retries):
            try:
                response = urllib.request.urlopen(f'{AI_PAL_URL}/health', timeout=5)
                if response.getcode() == 200:
                    return True
            except Exception:
                if i % 5 == 0:
                    self._update_status(f"Waiting for API... ({i+1}/{retries})", "info")
                time.sleep(2)

        return False

    def get_services_status(self) -> Dict[str, Any]:
        """Get current services status"""
        return {
            k: {**asdict(v), 'status': v.status.value}
            for k, v in self.services.items()
        }

    def get_error_history(self) -> List[Dict[str, Any]]:
        """Get error history"""
        return [
            {**asdict(e), 'severity': e.severity.value}
            for e in self.error_history
        ]

    def get_notifications(self) -> List[Dict[str, str]]:
        """Get notifications"""
        return [asdict(n) for n in self.notifications]

    def get_logs(self) -> List[str]:
        """Get application logs"""
        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, 'r') as f:
                    return f.readlines()[-100:]  # Last 100 lines
        except Exception as e:
            logger.error(f"Failed to read logs: {e}")
        return []

    def export_diagnostics(self) -> bool:
        """Export diagnostics to file"""
        try:
            diag_file = LOG_DIR / f'diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

            diagnostics = {
                'timestamp': datetime.now().isoformat(),
                'platform': PLATFORM,
                'services': self.get_services_status(),
                'errors': self.get_error_history(),
                'logs': self.get_logs(),
                'system_info': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent,
                }
            }

            with open(diag_file, 'w') as f:
                json.dump(diagnostics, f, indent=2, default=str)

            self._add_notification("Export", f"Diagnostics exported to {diag_file}", "success")
            return True
        except Exception as e:
            logger.error(f"Failed to export diagnostics: {e}")
            self._add_error(
                "Failed to export diagnostics",
                ErrorSeverity.WARNING,
                "EXPORT_FAILED",
                ["Check file permissions", "Ensure sufficient disk space"],
                str(e)
            )
            return False


# ============================================================================
# HTML UI Template
# ============================================================================

def get_html_controls() -> str:
    """Generate HTML control panel"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI-Pal Desktop</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                justify-content: flex-start;
                align-items: center;
                padding: 20px;
                overflow-y: auto;
            }

            .container {
                background: white;
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 700px;
                width: 100%;
                padding: 40px;
                margin: 20px 0;
            }

            .header {
                text-align: center;
                margin-bottom: 32px;
            }

            .logo {
                font-size: 40px;
                margin-bottom: 12px;
            }

            h1 {
                font-size: 28px;
                color: #333;
                margin-bottom: 4px;
                font-weight: 600;
            }

            .subtitle {
                color: #666;
                font-size: 14px;
            }

            .controls {
                display: flex;
                gap: 12px;
                margin-bottom: 32px;
            }

            button {
                flex: 1;
                padding: 14px 24px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }

            #btnStart {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }

            #btnStart:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }

            #btnStop {
                background: #f0f0f0;
                color: #333;
            }

            #btnStop:hover:not(:disabled) {
                background: #e8e8e8;
            }

            button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .section {
                margin-bottom: 24px;
            }

            .section-label {
                font-size: 12px;
                color: #999;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 12px;
                font-weight: 600;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .section-toggle {
                background: none;
                border: none;
                color: #667eea;
                cursor: pointer;
                font-size: 12px;
                padding: 4px 8px;
                border-radius: 4px;
                transition: background 0.2s;
            }

            .section-toggle:hover {
                background: #f0f0f0;
            }

            .section-content {
                display: block;
            }

            .section-content.hidden {
                display: none;
            }

            /* Status Section */
            #status {
                padding: 14px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
                background: #f5f5f5;
                color: #333;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            #status.info {
                background: #e3f2fd;
                color: #1976d2;
                border-left: 4px solid #1976d2;
            }

            #status.success {
                background: #e8f5e9;
                color: #388e3c;
                border-left: 4px solid #388e3c;
            }

            #status.error {
                background: #ffebee;
                color: #d32f2f;
                border-left: 4px solid #d32f2f;
            }

            /* Services Grid */
            .services-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 12px;
            }

            .service-card {
                padding: 14px;
                border-radius: 8px;
                background: white;
                border: 2px solid #e0e0e0;
                font-size: 13px;
                transition: all 0.2s ease;
            }

            .service-card:hover {
                border-color: #667eea;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
            }

            .service-name {
                font-weight: 600;
                margin-bottom: 6px;
                color: #333;
            }

            .service-port {
                font-size: 11px;
                color: #999;
                margin-bottom: 6px;
            }

            .service-status {
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 4px;
                display: inline-block;
                font-weight: 600;
            }

            .service-status.healthy {
                background: #c8e6c9;
                color: #2e7d32;
            }

            .service-status.degraded {
                background: #fff9c4;
                color: #f57f17;
            }

            .service-status.unhealthy {
                background: #ffcccc;
                color: #c62828;
            }

            .service-status.unknown {
                background: #f0f0f0;
                color: #666;
            }

            .status-history {
                display: flex;
                gap: 3px;
                margin: 6px 0;
                align-items: center;
            }

            .history-dot {
                display: inline-block;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                cursor: pointer;
                transition: transform 0.2s;
            }

            .history-dot:hover {
                transform: scale(1.3);
            }

            .history-dot.healthy {
                background-color: #2e7d32;
                opacity: 0.7;
            }

            .history-dot.degraded {
                background-color: #f57f17;
                opacity: 0.7;
            }

            .history-dot.unhealthy {
                background-color: #c62828;
                opacity: 0.7;
            }

            .history-dot.unknown {
                background-color: #999;
                opacity: 0.7;
            }

            .service-last-check {
                font-size: 10px;
                color: #bbb;
                margin-top: 6px;
            }

            /* Notifications */
            .notifications {
                margin-bottom: 24px;
            }

            .notifications-list {
                max-height: 180px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }

            .notification {
                padding: 12px 14px;
                border-radius: 8px;
                font-size: 13px;
                border-left: 4px solid;
                display: flex;
                justify-content: space-between;
                align-items: center;
                animation: slideIn 0.3s ease;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(-10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .notification-content {
                flex: 1;
            }

            .notification-title {
                font-weight: 600;
                margin-bottom: 2px;
            }

            .notification-message {
                font-size: 12px;
                opacity: 0.9;
            }

            .notification-close {
                background: none;
                border: none;
                color: inherit;
                cursor: pointer;
                font-size: 16px;
                padding: 0;
                margin-left: 8px;
                opacity: 0.6;
                transition: opacity 0.2s;
            }

            .notification-close:hover {
                opacity: 1;
            }

            .notification.success {
                background: #e8f5e9;
                border-color: #388e3c;
                color: #1b5e20;
            }

            .notification.error {
                background: #ffebee;
                border-color: #d32f2f;
                color: #b71c1c;
            }

            .notification.warning {
                background: #fff3e0;
                border-color: #f57c00;
                color: #e65100;
            }

            .notification.info {
                background: #e3f2fd;
                border-color: #1976d2;
                color: #0d47a1;
            }

            /* Errors Section */
            .errors-list {
                max-height: 300px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }

            .error-card {
                padding: 12px 14px;
                border-radius: 8px;
                border-left: 4px solid;
                background: white;
                border: 1px solid;
            }

            .error-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 8px;
            }

            .error-severity {
                display: inline-block;
                font-size: 10px;
                font-weight: 700;
                padding: 3px 8px;
                border-radius: 3px;
                text-transform: uppercase;
            }

            .error-severity.critical {
                background: #ffcdd2;
                color: #b71c1c;
            }

            .error-severity.warning {
                background: #ffe0b2;
                color: #e65100;
            }

            .error-severity.info {
                background: #bbdefb;
                color: #0d47a1;
            }

            .error-message {
                font-size: 13px;
                font-weight: 500;
                margin-bottom: 6px;
                color: #333;
            }

            .error-code {
                font-size: 11px;
                color: #999;
                font-family: monospace;
                margin-bottom: 6px;
            }

            .error-timestamp {
                font-size: 10px;
                color: #bbb;
                margin-bottom: 8px;
            }

            .error-suggestions {
                font-size: 12px;
                margin-bottom: 6px;
            }

            .error-suggestions-title {
                font-weight: 600;
                color: #555;
                margin-bottom: 4px;
            }

            .error-suggestions-list {
                list-style: none;
                margin-left: 12px;
                color: #666;
            }

            .error-suggestions-list li {
                margin: 2px 0;
                padding-left: 16px;
                position: relative;
            }

            .error-suggestions-list li:before {
                content: "→";
                position: absolute;
                left: 0;
                color: #667eea;
            }

            .error-details {
                font-size: 11px;
                color: #999;
                background: #f9f9f9;
                padding: 8px;
                border-radius: 4px;
                font-family: monospace;
                margin-top: 6px;
                max-height: 80px;
                overflow-y: auto;
            }

            .error-card.critical {
                border-color: #d32f2f;
                background: #ffebee;
            }

            .error-card.warning {
                border-color: #f57c00;
                background: #fff3e0;
            }

            .error-card.info {
                border-color: #1976d2;
                background: #e3f2fd;
            }

            .empty-state {
                text-align: center;
                padding: 20px;
                color: #999;
                font-size: 13px;
            }

            /* Spinner */
            .spinner {
                display: inline-block;
                width: 12px;
                height: 12px;
                border: 2px solid #f3f3f3;
                border-top: 2px solid #667eea;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Scrollbar styling */
            ::-webkit-scrollbar {
                width: 6px;
            }

            ::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb {
                background: #ccc;
                border-radius: 4px;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: #999;
            }

            .version {
                text-align: center;
                color: #999;
                font-size: 12px;
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid #e0e0e0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🤖</div>
                <h1>AI-Pal</h1>
                <p class="subtitle">Desktop Application Manager</p>
            </div>

            <div class="controls">
                <button id="btnStart" onclick="pywebview.api.start_server()">▶ Start Services</button>
                <button id="btnStop" onclick="pywebview.api.stop_server()">⏹ Stop Services</button>
            </div>

            <div class="section">
                <div class="status-label">Status</div>
                <div id="status" class="info">
                    <span class="spinner" id="statusSpinner" style="display:none;"></span>
                    <span id="statusText">Idle</span>
                </div>
            </div>

            <div class="section">
                <div class="section-label">
                    <span>Services</span>
                    <button class="section-toggle" onclick="toggleSection('services')">▼</button>
                </div>
                <div class="section-content" id="services-section">
                    <div class="services-grid" id="services">
                        <div class="empty-state">No services started yet</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-label">
                    <span>Notifications</span>
                    <button class="section-toggle" onclick="toggleSection('notifications')">▼</button>
                </div>
                <div class="section-content" id="notifications-section">
                    <div class="notifications-list" id="notifications">
                        <div class="empty-state">No notifications yet</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-label">
                    <span>Issues & Errors</span>
                    <button class="section-toggle" onclick="toggleSection('errors')">▼</button>
                </div>
                <div class="section-content hidden" id="errors-section">
                    <div class="errors-list" id="errors">
                        <div class="empty-state">✓ No errors detected</div>
                    </div>
                </div>
            </div>

            <div class="version">v1.0.0 | AI-Pal Desktop</div>
        </div>

        <script>
            let notificationTimeout = null;

            function updateStatus(message, type = 'info', showSpinner = false) {
                const status = document.getElementById('status');
                const statusText = document.getElementById('statusText');
                const spinner = document.getElementById('statusSpinner');

                statusText.textContent = message;
                status.className = type;
                spinner.style.display = showSpinner ? 'inline-block' : 'none';
            }

            function setControls(disabled) {
                document.getElementById('btnStart').disabled = disabled;
                document.getElementById('btnStop').disabled = disabled;
            }

            function toggleSection(sectionId) {
                const section = document.getElementById(sectionId + '-section');
                section.classList.toggle('hidden');
            }

            function updateServices(services) {
                const container = document.getElementById('services');
                if (!services || Object.keys(services).length === 0) {
                    container.innerHTML = '<div class="empty-state">No services started yet</div>';
                    return;
                }

                container.innerHTML = Object.entries(services).map(([key, service]) => {
                    const lastCheck = service.last_check || 'Never';
                    const portInfo = service.port ? `<div class="service-port">Port: ${service.port}</div>` : '';

                    // Generate status history visualization
                    let statusHistory = '';
                    if (service.status_history && service.status_history.length > 0) {
                        const historyDots = service.status_history.slice(-5).map(h => {
                            const statusClass = h.status || 'unknown';
                            return `<span class="history-dot ${statusClass}" title="${h.status} at ${new Date(h.timestamp).toLocaleTimeString()}"></span>`;
                        }).join('');
                        statusHistory = `<div class="status-history">${historyDots}</div>`;
                    }

                    return `
                        <div class="service-card">
                            <div class="service-name">${service.name}</div>
                            ${portInfo}
                            <div class="service-status ${service.status}">${service.status.toUpperCase()}</div>
                            ${statusHistory}
                            <div class="service-last-check">Last check: ${lastCheck}</div>
                        </div>
                    `;
                }).join('');
            }

            function addNotification(title, message, type = 'info', autoDismiss = true) {
                const container = document.getElementById('notifications');

                // Clear empty state
                if (container.querySelector('.empty-state')) {
                    container.innerHTML = '';
                }

                const notification = document.createElement('div');
                notification.className = `notification ${type}`;
                notification.innerHTML = `
                    <div class="notification-content">
                        <div class="notification-title">${title}</div>
                        <div class="notification-message">${message}</div>
                    </div>
                    <button class="notification-close" onclick="this.parentElement.remove()">✕</button>
                `;

                container.insertBefore(notification, container.firstChild);

                // Auto-dismiss after 5 seconds
                if (autoDismiss) {
                    setTimeout(() => {
                        notification.style.opacity = '0';
                        notification.style.transform = 'translateY(-10px)';
                        setTimeout(() => notification.remove(), 300);
                    }, 5000);
                }
            }

            function updateNotifications(notifications) {
                const container = document.getElementById('notifications');
                if (!notifications || notifications.length === 0) {
                    container.innerHTML = '<div class="empty-state">No notifications yet</div>';
                    return;
                }

                container.innerHTML = notifications.map(n => `
                    <div class="notification ${n.notification_type}">
                        <div class="notification-content">
                            <div class="notification-title">${n.title}</div>
                            <div class="notification-message">${n.message}</div>
                        </div>
                        <button class="notification-close" onclick="this.parentElement.remove()">✕</button>
                    </div>
                `).join('');
            }

            function updateErrors(errors) {
                const container = document.getElementById('errors');
                const section = document.getElementById('errors-section');

                if (!errors || errors.length === 0) {
                    container.innerHTML = '<div class="empty-state">✓ No errors detected</div>';
                    section.classList.add('hidden');
                    return;
                }

                section.classList.remove('hidden');
                container.innerHTML = errors.map(err => {
                    const suggestions = err.suggestions && err.suggestions.length > 0
                        ? `<div class="error-suggestions">
                            <div class="error-suggestions-title">💡 Suggestions:</div>
                            <ul class="error-suggestions-list">
                                ${err.suggestions.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                        </div>`
                        : '';

                    const details = err.details
                        ? `<div class="error-details">${err.details}</div>`
                        : '';

                    return `
                        <div class="error-card ${err.severity}">
                            <div class="error-header">
                                <div class="error-message">${err.message}</div>
                                <span class="error-severity ${err.severity}">${err.severity}</span>
                            </div>
                            <div class="error-code">Error code: ${err.code}</div>
                            <div class="error-timestamp">Time: ${new Date(err.timestamp).toLocaleTimeString()}</div>
                            ${suggestions}
                            ${details}
                        </div>
                    `;
                }).join('');
            }

            // Initialize
            updateStatus('Idle', 'info', false);
            setControls(false);
        </script>
    </body>
    </html>
    '''


# ============================================================================
# Application Entry Point
# ============================================================================

def main() -> None:
    """Main application entry point"""
    logger.info("="*70)
    logger.info("AI-Pal Desktop Application Starting")
    logger.info("="*70)

    # Create API instance
    api = DesktopAppAPI()

    # Create main window
    window = webview.create_window(
        'AI-Pal',
        html=get_html_controls(),
        js_api=api,
        width=700,
        height=900,
        min_size=(600, 700)
    )

    # Set window reference
    api.set_window(window)

    # Cleanup handler
    def on_closing():
        logger.info("Window closing, cleaning up...")
        api.stop_server()
        logger.info("AI-Pal Desktop Application closed")

    window.events.closing += on_closing

    # Start application
    webview.start(debug=False)


if __name__ == '__main__':
    main()
