'''custom loadbalancer and reverse proxy implementation'''

import json
import itertools

from pathlib import Path

import httpx

from fastapi import FastAPI, Request, Response

app = FastAPI()

# gets deployment states
STATE_FILE = (
    Path(__file__).resolve().parent.parent
    / "builder"
    / "deployment_state.json"
)

counter = itertools.count()

# gets the deployed and running backend
def get_backends():
    with open(STATE_FILE, "r") as f:
        state = json.load(f)
    active = state["active"]
    if active is None:
        return []
    return state[active]["ports"]

# recieves all the requests
@app.api_route(
    "/{path:path}",
    methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE"
    ]
)
async def proxy(
    request: Request,
    path: str
):
    ports = get_backends()
    if not ports:
        return Response(
            content="No deployment available",
            status_code=503
        )
    # round robin request forwarding
    index = next(counter)
    port = ports[
        index % len(ports)
    ]
    target_url = (
        f"http://127.0.0.1:{port}/{path}"
    )
    if request.url.query:
        target_url += (
            f"?{request.url.query}"
        )
    body = await request.body()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                content=body,
                headers={
                    key: value
                    for key, value
                    in request.headers.items()
                    if key.lower() != "host"
                },
                timeout=10
            )
        except httpx.RequestError:
            return Response(
                content="Backend unavailable",
                status_code=502
            )

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers={
            key: value
            for key, value
            in response.headers.items()
            if key.lower()
            not in [
                "content-length",
                "transfer-encoding",
                "connection"
            ]
        }
    )