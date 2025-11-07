"""
Dashboard integration module for serving the React dashboard from FastAPI.

This module provides utilities to integrate the built React dashboard
with the FastAPI application for both development and production.
"""

from pathlib import Path
from typing import Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import logging

logger = logging.getLogger(__name__)


def integrate_dashboard(
    app: FastAPI,
    dashboard_path: Optional[Path] = None,
    base_path: str = "/dashboard"
) -> bool:
    """
    Integrate the React dashboard with the FastAPI application.

    Args:
        app: FastAPI application instance
        dashboard_path: Path to the built dashboard dist directory.
                       Defaults to <project_root>/dashboard/dist
        base_path: URL path where dashboard will be served (default: /dashboard)

    Returns:
        bool: True if successfully integrated, False otherwise

    Example:
        ```python
        from fastapi import FastAPI
        from src.dashboard_integration import integrate_dashboard

        app = FastAPI()

        # Integrate dashboard
        if integrate_dashboard(app):
            logger.info("Dashboard integrated successfully")
        else:
            logger.warning("Dashboard not found - skipping integration")
        ```
    """
    if dashboard_path is None:
        # Default to dashboard/dist relative to project root
        project_root = Path(__file__).parent.parent
        dashboard_path = project_root / "dashboard" / "dist"

    dashboard_path = Path(dashboard_path).resolve()

    # Check if dashboard exists
    if not dashboard_path.exists():
        logger.warning(
            f"Dashboard not found at {dashboard_path}. "
            "Build the dashboard with 'npm run build' in the dashboard directory."
        )
        return False

    index_html = dashboard_path / "index.html"
    if not index_html.exists():
        logger.warning(f"Dashboard index.html not found at {index_html}")
        return False

    try:
        # Mount static files
        app.mount(
            base_path,
            StaticFiles(directory=str(dashboard_path), html=True),
            name="dashboard"
        )

        logger.info(f"Dashboard integrated successfully at {base_path}")
        logger.info(f"Dashboard path: {dashboard_path}")

        # Add catch-all route for SPA routing
        @app.get(f"{base_path}" + "/{full_path:path}")
        async def serve_dashboard(full_path: str):
            """Serve dashboard index.html for SPA routing"""
            return FileResponse(index_html)

        return True

    except Exception as e:
        logger.error(f"Failed to integrate dashboard: {str(e)}")
        return False


def get_dashboard_static_path() -> Optional[Path]:
    """
    Get the path to the dashboard static files directory.

    Returns:
        Path to dashboard dist directory if it exists, None otherwise
    """
    project_root = Path(__file__).parent.parent
    dashboard_path = project_root / "dashboard" / "dist"

    if dashboard_path.exists():
        return dashboard_path

    return None


def is_dashboard_available() -> bool:
    """
    Check if the dashboard is built and available for serving.

    Returns:
        bool: True if dashboard dist exists and contains index.html
    """
    dashboard_path = get_dashboard_static_path()
    if dashboard_path is None:
        return False

    return (dashboard_path / "index.html").exists()
