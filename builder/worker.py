import time
import subprocess
from pathlib import Path

from buildQueue import Queue


def worker():
    print("Build worker started")
    while True:
        pending_items = Queue.get_pending()
        if not pending_items:
            time.sleep(2)
            continue

        cur_build = pending_items[0]
        deployment_id = cur_build["id"]
        print(f"Starting build: {deployment_id}")
        Queue.update_item_status(
            deployment_id,
            "in_progress"
        )
        deployment_dir = (
            Path(__file__).resolve().parent.parent
            / "deployments"
            / deployment_id
        )
        try:
            deployment_dir.mkdir(
                parents=True,
                exist_ok=True
            )

            print(f"Cloning {cur_build['url']}")

            subprocess.run(
                [
                    "git",
                    "clone",
                    cur_build["url"],
                    "."
                ],
                cwd=deployment_dir,
                check=True
            )
            print("Clone Done")
            
            Queue.update_item_status(
                deployment_id,
                "completed"
            )
            print(f"Build completed: {deployment_id}")

        except Exception as e:
            print(f"Build failed: {deployment_id}: {e}")
            Queue.update_item_status(
                deployment_id,
                "failed"
            )
            
if __name__ == "__main__":
    worker()