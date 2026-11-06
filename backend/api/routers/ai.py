import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from api.deps import CurrentUser,current_user
from api.schemas import AIRequest,ExportRequest
from docx import Document
from openpyxl import Workbook

router=APIRouter(prefix="/ai",tags=["ai"])

@router.post("/assist")
async def assist(body:AIRequest,cu:CurrentUser=Depends(current_user)):
    # Production provider integration belongs here. This deterministic fallback keeps the endpoint functional without exposing API secrets.
    title=body.task.strip() or "AI Assistance"
    content=f"{title}\n\nAuthorized Context\n{body.context or 'No additional context supplied.'}\n\nWorking Draft\nThis is a human-review draft generated through the Tech4Future-Global AI service layer. Verify evidence, figures, legal requirements, safeguarding requirements, donor terms, and approval authority before final use."
    return {"output":content,"provider":"server-fallback","human_review_required":True}

@router.post("/export")
async def export(body:ExportRequest,cu:CurrentUser=Depends(current_user)):
    if body.format=="excel":
        wb=Workbook(); ws=wb.active; ws.title="AI Draft"; ws.append(["Tech4Future-Global",body.title]); ws.append(["Status","AI working draft — human review required"]); ws.append([])
        for line in body.content.splitlines(): ws.append([line])
        stream=io.BytesIO(); wb.save(stream); stream.seek(0)
        return StreamingResponse(stream,media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",headers={"Content-Disposition":f'attachment; filename="{body.title[:70] or "AI-Draft"}.xlsx"'})
    doc=Document(); doc.add_heading("TECH4FUTURE-GLOBAL",0); doc.add_heading(body.title,1); doc.add_paragraph("AI working draft — human review required")
    for line in body.content.splitlines(): doc.add_paragraph(line)
    stream=io.BytesIO(); doc.save(stream); stream.seek(0)
    return StreamingResponse(stream,media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",headers={"Content-Disposition":f'attachment; filename="{body.title[:70] or "AI-Draft"}.docx"'})
