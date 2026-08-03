"""Health check for the applications"""

import time
import requests


def health_check(port, retries=10):

    for _ in range(retries):

        try:
            response = requests.get(
                f"http://127.0.0.1:{port}/health",
                timeout=2
            )

            if response.status_code == 200:
                return True

        except requests.RequestException:
            pass

        time.sleep(1)

    return False


def check_instances(ports):

    for port in ports:

        if not health_check(port):
            return False

    return True