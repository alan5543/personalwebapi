import socket
import httpx
from fastapi import FastAPI, HTTPException
from telegram import Bot
from telegram.error import TelegramError
from pydantic import BaseModel
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
import logging

app = FastAPI()
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MessageData(BaseModel):
    name: str
    email: str
    message: str

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Telegram backend is running",
        "timestamp": datetime.now(timezone.utc).isoformat() + " UTC"
    }

@app.get("/test-dns")
async def test_dns():
    try:
        ip = socket.gethostbyname("api.telegram.org")
        logger.info(f"DNS resolved: api.telegram.org -> {ip}")
        return {"status": "success", "ip": ip}
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed: {str(e)}")
        return {"status": "error", "details": str(e)}

@app.get("/test-network")
async def test_network():
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get("https://api.ipify.org?format=json")
            logger.info(f"Network test successful: {response.json()}")
            return {"status": "success", "data": response.json()}
    except httpx.HTTPError as e:
        logger.error(f"Network test failed: {str(e)}")
        return {"status": "error", "details": str(e)}

@app.post("/send-message")
async def send_message(data: MessageData):
    try:
        name = data.name.strip()
        email = data.email.strip()
        message = data.message.strip()

        if not all([name, email, message]):
            raise HTTPException(status_code=400, detail="All fields must not be empty")
        if len(message) > 4096:
            raise HTTPException(status_code=400, detail="Message exceeds 4096 character limit")
        if '@' not in email or '.' not in email.split('@')[1]:
            raise HTTPException(status_code=400, detail="Invalid email format")

        timestamp = datetime.now(timezone.utc).isoformat().split('.')[0] + " UTC"
        telegram_message = (
            f"*New Message*\n"
            f"_Received on: {timestamp}_\n"
            f"---\n"
            f"*Sender Details:*\n"
            f"- *Name:* {name}\n"
            f"- *Email:* {email}\n"
            f"---\n"
            f"*Message:*\n"
            f"{message}"
        )

        logger.debug(f"Sending message to chat_id: {TELEGRAM_CHAT_ID}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            bot = Bot(token=TELEGRAM_BOT_TOKEN, client=client)
            try:
                await bot.send_message(
                    chat_id=TELEGRAM_CHAT_ID,
                    text=telegram_message,
                    parse_mode="Markdown",
                    disable_notification=True
                )
                logger.info("Message sent successfully")
                return {"success": True, "message": "Message sent to Telegram"}
            except TelegramError as e:
                logger.error(f"TelegramError: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)