from pydantic import BaseModel, Field


class ProjectInfo(BaseModel):
    title: str
    description: str
    target_population: str | None = None
    goals: list[str] = Field(default_factory=list)
    timeline: str | None = None
    requested_amount: float | None = None
    budget_notes: str | None = None


class FunderInfo(BaseModel):
    name: str
    # Optional when an RFP document is uploaded instead (see /grants/draft/upload).
    rfp_requirements: str | None = None
    focus_areas: list[str] = Field(default_factory=list)
    word_or_page_limit: str | None = None


class GrantDraftRequest(BaseModel):
    project: ProjectInfo
    funder: FunderInfo


class GrantDraftResponse(BaseModel):
    id: int
    created_at: str
    draft: str


class DraftSummary(BaseModel):
    id: int
    created_at: str
    organization_name: str
    project_title: str
    funder_name: str


class DraftDetail(DraftSummary):
    draft: str
    request: GrantDraftRequest
