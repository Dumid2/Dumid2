import logging
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

from app import db
from app.grant_agent import generate_grant_draft, generate_grant_draft_with_documents
from app.org_profile_loader import ORG_NAME
from app.schemas import (
    DraftDetail,
    DraftSummary,
    GrantDraftRequest,
    GrantDraftResponse,
)

logger = logging.getLogger(__name__)

app = FastAPI(title="Grant Writing Agent")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

MAX_PDF_SIZE = 32 * 1024 * 1024  # Anthropic's per-request PDF size limit
MAX_SUPPORTING_DOCS = 10


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.environ.get("APP_API_KEY")
    if not expected:
        raise HTTPException(status_code=500, detail="APP_API_KEY is not configured on the server.")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


@app.on_event("startup")
def on_startup() -> None:
    db.init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _save_draft(request: GrantDraftRequest, draft: str) -> GrantDraftResponse:
    row = db.save_draft(
        organization_name=ORG_NAME,
        project_title=request.project.title,
        funder_name=request.funder.name,
        request_json=request.model_dump_json(),
        draft=draft,
    )
    return GrantDraftResponse(id=row["id"], created_at=row["created_at"], draft=draft)


@app.post("/grants/draft", response_model=GrantDraftResponse, dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
def draft_grant(request: Request, body: GrantDraftRequest) -> GrantDraftResponse:
    if not body.funder.rfp_requirements:
        raise HTTPException(
            status_code=400,
            detail="funder.rfp_requirements is required (or use /grants/draft/upload "
            "to attach an RFP document instead).",
        )
    try:
        draft = generate_grant_draft(body)
    except Exception:
        logger.exception("Grant draft generation failed for funder=%s", body.funder.name)
        raise HTTPException(
            status_code=502, detail="Draft generation failed; check server logs."
        ) from None
    return _save_draft(body, draft)


@app.get(
    "/grants/drafts",
    response_model=list[DraftSummary],
    dependencies=[Depends(require_api_key)],
)
def list_drafts(limit: int = 20, offset: int = 0) -> list[DraftSummary]:
    rows = db.list_drafts(limit=limit, offset=offset)
    return [DraftSummary(**dict(row)) for row in rows]


@app.get(
    "/grants/drafts/{draft_id}",
    response_model=DraftDetail,
    dependencies=[Depends(require_api_key)],
)
def get_draft(draft_id: int) -> DraftDetail:
    row = db.get_draft(draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")
    return DraftDetail(
        id=row["id"],
        created_at=row["created_at"],
        organization_name=row["organization_name"],
        project_title=row["project_title"],
        funder_name=row["funder_name"],
        draft=row["draft"],
        request=GrantDraftRequest.model_validate_json(row["request_json"]),
    )


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
    if not data.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail=f"'{file.filename}' does not look like a real PDF file.",
        )
    return data


@app.post(
    "/grants/draft/upload",
    response_model=GrantDraftResponse,
    dependencies=[Depends(require_api_key)],
)
@limiter.limit("10/minute")
async def draft_grant_with_documents(
    request: Request,
    body: str = Form(
        ..., description="JSON matching GrantDraftRequest (rfp_requirements optional)"
    ),
    rfp_document: UploadFile | None = File(None),
    supporting_documents: list[UploadFile] = File(default=[]),
) -> GrantDraftResponse:
    if len(supporting_documents) > MAX_SUPPORTING_DOCS:
        raise HTTPException(
            status_code=400,
            detail=f"At most {MAX_SUPPORTING_DOCS} supporting documents are allowed "
            f"(got {len(supporting_documents)}).",
        )

    try:
        parsed_request = GrantDraftRequest.model_validate_json(body)
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
    except Exception:
        logger.exception(
            "Grant draft generation (upload) failed for funder=%s", parsed_request.funder.name
        )
        raise HTTPException(
            status_code=502, detail="Draft generation failed; check server logs."
        ) from None
    return _save_draft(parsed_request, draft)
