from fastapi import FastAPI, Request
import dotenv
app = FastAPI()

dotenv.load_dotenv()
git_webhook_secret = dotenv.get_key(".env", "GIT_WEBHOOK_SECRET")

@app.get("/")
async def root(request: Request):
    print(request.body)
    return {"message": "Hello World"}

@app.post("/")
async def webhook(request: Request):
    x: bytes = await request.body()
    print(x)
    return {"message": "Hello World"}