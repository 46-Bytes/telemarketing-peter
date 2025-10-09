import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from routes.calender_route import router as calender_router
from routes.prospects_route import router as prospects_router
from routes.send_ebook_route import router as send_ebook_router
from routes.auth_route import router as auth_router
from routes.stats_route import router as stats_router
from routes.campaign_route import router as campaign_router
from routes.microsoft_routes import router as microsoft_router
from routes.upload_route import router as upload_router
from routes.user_route import router as user_router
from routes.appointment_email_route import appointment_email_router
from routes.benchmark_route import benchmark_router
from services.prospect_service import update_prospect_call_info
from fastapi.middleware.cors import CORSMiddleware
import threading
from jobs.run_scheduler import run_scheduler
import uvicorn
from pathlib import Path
from config.cloudinary_config import configure_cloudinary
import logging
from retell import Retell

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

retell = Retell(api_key=os.getenv("RETELL_API_KEY"))

app = FastAPI(title="Sales Agent Backend")

# Create public directory if it doesn't exist (for backward compatibility)
# Note: New uploads will use Cloudinary instead of local storage
public_dir = Path("public")
public_dir.mkdir(exist_ok=True)
ebooks_dir = public_dir / "ebooks"
ebooks_dir.mkdir(exist_ok=True)

# Mount static files directory (for backward compatibility)
app.mount("/ebooks", StaticFiles(directory="public/ebooks"), name="ebooks")

# Configure Cloudinary (preferred method for file storage)
cloudinary_configured = configure_cloudinary()
if cloudinary_configured:
    logger.info("Cloudinary configured successfully")
else:
    logger.warning("Cloudinary configuration failed or not provided - falling back to local storage")

# Start the scheduler only if not running on Vercel
is_vercel = os.environ.get('VERCEL') == '1'
if not is_vercel:
    # Start the unified scheduler in a separate thread for cron
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(prospects_router, prefix="/api") 
app.include_router(calender_router, prefix="/calendar")
app.include_router(send_ebook_router, prefix="/send_ebook")
app.include_router(stats_router, prefix="/stats")
app.include_router(auth_router, prefix="/auth")
app.include_router(campaign_router, prefix="/campaign")
app.include_router(microsoft_router)  # No prefix needed as it's defined in the router
app.include_router(upload_router, prefix="")
app.include_router(user_router, prefix="/users")
app.include_router(appointment_email_router)
app.include_router(benchmark_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Sales Agent Backend"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    logger.info(f"Webhook received: {data}")
    if data["event"] == "call_analyzed":
        result = await update_prospect_call_info(data)
    return {"message": "Webhook received"}

if __name__ == "__main__":
    # Get port from environment variable or use default 8000
    port = int(os.getenv("PORT", 8080))
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True  # Enable auto-reload during development
    )