"""Welcome — the full-screen landing shown before the dashboard.

This is the root/default route. It renders through the shared landing
component only; streamlit_app.py suppresses the sidebar and the boundary
ribbon on this route, and every dashboard page keeps the normal shell.
"""

from __future__ import annotations

from dashboard.components.landing_page import render_landing

render_landing()
