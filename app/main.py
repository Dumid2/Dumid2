from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

load_dotenv()

from app.grant_agent import generate_grant_draft, generate_grant_draft_with_documents
from app.schemas import GrantDraftRequest, GrantDraftResponse

app = FastAPI(title="Grant Writing Agent")

MAX_PDF_SIZE = 32 * 1024 * 1024  # Anthropic's per-request PDF size limit


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/grants/draft", response_model=GrantDraftResponse)
def draft_grant(request: GrantDraftRequest) -> GrantDraftResponse:
    if not request.funder.rfp_requirements:
        raise HTTPException(
            status_code=400,
            detail="funder.rfp_requirements is required (or use /grants/draft/upload "
            "to attach an RFP document instead).",
        )
    try:
        draft = generate_grant_draft(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GrantDraftResponse(draft=draft)


async def _read_pdf(file: UploadFile) -> bytes:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail=f"'{file.filename}' must be a PDF (got {file.content_type}).",
        )
    data = await file.read()
    if len(data) > MAX_PDF_SIZE:
        raise HTTPException(
            status_code=400, detail=f"'{file.filename}' exceeds the 32MB size limit."
        )
    return data


@app.post("/grants/draft/upload", response_model=GrantDraftResponse)
async def draft_grant_with_documents(
    request: str = Form(
        ..., description="JSON matching GrantDraftRequest (rfp_requirements optional)"
    ),
    rfp_document: UploadFile | None = File(None),
    supporting_documents: list[UploadFile] = File(default=[]),
) -> GrantDraftResponse:
    try:
        parsed_request = GrantDraftRequest.model_validate_json(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid request JSON: {exc}") from exc

    if not parsed_request.funder.rfp_requirements and rfp_document is None:
        raise HTTPException(
            status_code=400,
            detail="Provide funder.rfp_requirements or an rfp_document upload.",
        )

    rfp_pdf = await _read_pdf(rfp_document) if rfp_document else None
    supporting_pdfs = [
        (f.filename or "supporting document", await _read_pdf(f))
        for f in supporting_documents
    ]

    try:
        draft = generate_grant_draft_with_documents(
            parsed_request, rfp_pdf=rfp_pdf, supporting_pdfs=supporting_pdfs
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GrantDraftResponse(draft=draft)
