'''File for deployment'''

import os
import subprocess
from pathlib import Path

from deployment_state import get_state, save_state
from health import check_instances


BLUE_PORTS = [3001, 3002]
GREEN_PORTS = [3003, 3004]


def start_instance(deployment_dir: Path, port: int):
    '''starts an instance'''
    env = os.environ.copy()
    env["PORT"] = str(port)

    process = subprocess.Popen(
        ["node", "index.js"],
        cwd=deployment_dir,
        env=env
    )

    return process


def stop_processes(processes):
    '''stops the process with pid'''
    for process in processes:

        try:
            process.terminate()
        except Exception:
            pass


def deploy(deployment_id: str, deployment_dir: Path):
    '''deploys the project/package'''
    
    # get the states of current deployments
    state = get_state()


    if state["active"] == "blue":
        target = "green"
        ports = GREEN_PORTS

    else:
        target = "blue"
        ports = BLUE_PORTS


    print(f"Deploying {deployment_id} to {target}")
    print(f"Ports: {ports}")


    # starts the instance and pushes their pids
    processes = []
    
    for port in ports:
        process = start_instance(
            deployment_dir,
            port
        )

        processes.append(process)


    # healthcheck for deployments
    print("Checking health...")

    if not check_instances(ports):

        print("Health check failed")

        stop_processes(processes)

        raise RuntimeError(
            "New deployment unhealthy"
        )


    print("Health check passed")

    state[target] = {
        "deployment_id": deployment_id,
        "ports": ports,
        "pids": [
            process.pid
            for process in processes
        ]
    }

    state["active"] = target

    save_state(state)

    print(
        f"Traffic switched to {target}"
    )
    

def rollback():
    '''Rollback from current active state to previous if any issues found'''
    
    state = get_state()
    active = state["active"]

    if active == "blue":
        previous = "green"
    else:
        previous = "blue"

    if state[previous] is None:
        raise RuntimeError(
            "No previous deployment available"
        )

    ports = state[previous]["ports"]

    if not check_instances(ports):

        raise RuntimeError(
            "Previous deployment is unhealthy"
        )

    state["active"] = previous

    save_state(state)

    print(
        f"Rolled back to {previous}"
    )