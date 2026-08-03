'''
File for deployment state operations
'''


import json
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "deployment_state.json"

# gets the current states of deployments
def get_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

# saves the deployment 
def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# gets active deployment states
def get_active():
    state = get_state()

    active = state["active"]

    if active is None:
        return None

    return state[active]

# changes active from green to blue and vice versa
def switch_active(slot):
    state = get_state()
    state["active"] = slot
    save_state(state)