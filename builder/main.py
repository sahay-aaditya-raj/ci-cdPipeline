import logging
import hashlib
import hmac
import os
import threading

from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv

from buildQueue import Queue
from worker import worker


BASE_DIR = Path(__file__).resolve().parent

VERSION_FILE = BASE_DIR / ".version"

load_dotenv(BASE_DIR / ".env")

git_webhook_secret = os.getenv(
    "GIT_WEBHOOK_SECRET"
)

if not git_webhook_secret:
    raise RuntimeError(
        "GIT_WEBHOOK_SECRET not found"
    )

url = os.getenv(
    "REPO_URL"
)
if not url:
    raise RuntimeError(
        "REPO_URL not found"
    )
    
logging.basicConfig(
    filename="gitWebhook.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s"
)


try:
    version = int(
        VERSION_FILE.read_text().strip()
    )

except (FileNotFoundError, ValueError):
    version = 1

    VERSION_FILE.write_text(
        str(version)
    )


worker_thread = threading.Thread(
    target=worker,
    daemon=True
)

worker_thread.start()

app = FastAPI()


@app.get("/health")
def health():
    return {
        "message": "Running"
    }


@app.get("/queue")
def get_queue():
    return {
        "queue": Queue.get_queue()
    }


@app.post("/")
async def webhook(request: Request):

    global version

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not signature:
        raise HTTPException(
            status_code=400,
            detail="Missing signature"
        )

    body = await request.body()

    expected = (
        "sha256="
        + hmac.new(
            git_webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
    )

    if not hmac.compare_digest(
        signature,
        expected
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    payload = await request.json()

    event = request.headers.get(
        "X-GitHub-Event"
    )

    if event != "push":
        return {
            "message": "Event ignored"
        }

    commit_id = payload.get("after")

    if not commit_id:
        raise HTTPException(
            status_code=400,
            detail="Missing commit ID"
        )

    logging.info(
        f"before: {payload.get('before')}"
    )

    logging.info(
        f"after: {commit_id}"
    )

    logging.info(
        f"event: {event}"
    )

    Queue.add_item({
        "id": commit_id,
        "status": "pending",
        "url": url,
        "version": version
    })

    version += 1

    VERSION_FILE.write_text(
        str(version)
    )

    return {
        "message": "Build queued",
        "id": commit_id
    }