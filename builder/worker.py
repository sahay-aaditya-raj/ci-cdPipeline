'''main worker file that builds and deploys'''

import time
import subprocess

from pathlib import Path

from buildQueue import Queue
from deployer import deploy


def worker():
    print("Build worker started")
    while True:
        pending_items = Queue.get_pending()

        if not pending_items:
            time.sleep(2)
            continue

        cur_build = pending_items[0]

        deployment_id = cur_build["id"]
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
            # clones the project
            deployment_dir.mkdir(
                parents=True,
                exist_ok=True
            )
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
            # installs dependencies
            subprocess.run(
                [
                    "npm",
                    "ci"
                ],
                cwd=deployment_dir,
                check=True
            )
            # deplpoys the project
            deploy(
                deployment_id,
                deployment_dir
            )

            # updates the deployment status
            Queue.update_item_status(
                deployment_id,
                "completed"
            )

            print(
                f"Deployment completed: {deployment_id}"
            )

        except Exception as e:

            print(
                f"Deployment failed: {e}"
            )

            Queue.update_item_status(
                deployment_id,
                "failed"
            )


if __name__ == "__main__":
    worker()