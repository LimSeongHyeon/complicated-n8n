import subprocess
import json
import re
import sys
import logging
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

SCRIPTS_DIR = Path("/scripts")
SCRIPTS_REQUIREMENTS = SCRIPTS_DIR / "requirements.txt"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# 설치 중 요청이 들어오는 경우를 대비한 락
_install_lock = threading.Lock()
# 현재 설치된 스크립트 패키지 추적
_script_packages: set[str] = set()


def _parse_package_names(path: Path) -> set[str]:
    names = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            name = re.split(r"[=<>!~\[\s]", line)[0].strip()
            if name:
                names.add(name.lower())
    return names


def install_requirements():
    global _script_packages
    if not SCRIPTS_REQUIREMENTS.exists():
        return

    with _install_lock:
        new_packages = _parse_package_names(SCRIPTS_REQUIREMENTS)
        removed = _script_packages - new_packages

        if removed:
            logger.info("Uninstalling removed packages: %s", removed)
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y"] + sorted(removed),
                capture_output=True,
                text=True,
            )

        logger.info("Running pip install -r scripts/requirements.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(SCRIPTS_REQUIREMENTS)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            logger.info("pip install completed successfully.")
            _script_packages = new_packages
        else:
            logger.error("pip install failed:\n%s", result.stderr.strip())


class RequirementsHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if Path(event.src_path).name == "requirements.txt":
            install_requirements()

    def on_created(self, event):
        if Path(event.src_path).name == "requirements.txt":
            install_requirements()


@app.on_event("startup")
def startup():
    # 앱 시작 시 최초 1회 설치
    install_requirements()

    # 파일 감시 시작
    observer = Observer()
    observer.schedule(RequirementsHandler(), path=str(SCRIPTS_DIR), recursive=False)
    observer.daemon = True
    observer.start()
    logger.info("Watching %s for requirements.txt changes.", SCRIPTS_DIR)


class RunRequest(BaseModel):
    scriptName: str
    parameters: dict[str, Any] = {}


@app.post("/run")
def run_script(req: RunRequest):
    script_path = SCRIPTS_DIR / req.scriptName

    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script '{req.scriptName}' not found in /scripts")

    if script_path.suffix != ".py":
        raise HTTPException(status_code=400, detail="Only .py scripts are allowed")

    args = [f"--{k}={v}" for k, v in req.parameters.items()]

    # 설치 중이라면 완료될 때까지 대기
    with _install_lock:
        cmd = [sys.executable, str(script_path)] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Script execution timed out (60s)")

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Script exited with non-zero code",
                "returncode": result.returncode,
                "stderr": result.stderr.strip(),
            },
        )

    try:
        output = json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Script output is not valid JSON. Script must print a dict as JSON.",
                "stdout": result.stdout.strip(),
            },
        )

    if not isinstance(output, dict):
        raise HTTPException(
            status_code=500,
            detail="Script output must be a JSON object (dict), not a list or primitive.",
        )

    return output
