from fastapi import FastAPI, Request, HTTPException
import dotenv
import hashlib
import hmac


app = FastAPI()

dotenv.load_dotenv()

git_webhook_secret = dotenv.get_key(".env", "GIT_WEBHOOK_SECRET")


log_file = 'gitWebhook.log'


@app.get("/")
async def root(request: Request):
    print(request.body)
    return {"message": "Hello World"}

@app.post("/")
async def webhook(request: Request):
    signature: str = request.headers.get("X-Hub-Signature-256")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")
    
    body: bytes = await request.body()

    expected = "sha256=" + hmac.new(
        git_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event: str = request.headers.get("X-Github-Event")


    print(body)
    with open(log_file, "a") as f:
        f.write(f'body: {payload}\n')
        f.write(f'event: {event}\n')
        f.write(f'signature: {signature}\n')
        
    
    return {"message": "Hello World"}