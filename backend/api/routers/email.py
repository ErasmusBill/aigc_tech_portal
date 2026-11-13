from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from asgiref.sync import sync_to_async
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger("api.email")
router = APIRouter(prefix="/email", tags=["email"])

class EmailPayload(BaseModel):
    to: str
    subject: str = "Tech4Future-Global Notification"
    text: Optional[str] = ""
    message: Optional[str] = ""
    html: Optional[str] = None

@router.post("/send")
async def send_email(payload: EmailPayload):
    recipient = payload.to.strip()
    if not recipient:
        raise HTTPException(status_code=400, detail="Recipient email ('to') is required")

    text_body = payload.text or payload.message or ""

    def _deliver():
        return send_mail(
            subject=payload.subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
            html_message=payload.html,
        )

    try:
        sent = await sync_to_async(_deliver, thread_sensitive=True)()
        return {"ok": True, "message": f"Email successfully delivered to {recipient}", "sent_count": sent}
    except Exception as exc:
        logger.error(f"Failed to deliver email to {recipient}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
