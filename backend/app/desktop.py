"""Serve the installed Angular build and API with one local production server."""
import os
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from app.main import app


class DesktopFiles(StaticFiles):
    async def get_response(self, path, scope):
        # Unknown API requests and missing assets must keep their HTTP errors.
        if path == "api" or path.startswith(("api/", "data/")):
            raise HTTPException(status_code=404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            accepts_html = any(
                key == b"accept" and b"text/html" in value
                for key, value in scope.get("headers", [])
            )
            if exc.status_code == 404 and accepts_html and not Path(path).suffix:
                return await super().get_response("index.html", scope)
            raise


app.mount("/", DesktopFiles(directory=os.environ["TMC_FRONTEND_DIR"], html=True), name="desktop")
