from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()

from app.grant_agent import generate_grant_draft
from app.schemas import GrantDraftRequest, GrantDraftResponse

app = FastAPI(title="Grant Writing Agent")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/grants/draft", response_model=GrantDraftResponse)
def draft_grant(request: GrantDraftRequest) -> GrantDraftResponse:
    try:
        draft = generate_grant_draft(request)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return GrantDraftResponse(draft=draft)
