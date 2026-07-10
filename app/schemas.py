from pydantic import BaseModel, Field


class OrganizationInfo(BaseModel):
    name: str
    mission: str
    ein: str | None = None
    years_operating: int | None = None
    past_grants: list[str] = Field(default_factory=list)


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
    organization: OrganizationInfo
    project: ProjectInfo
    funder: FunderInfo


class GrantDraftResponse(BaseModel):
    draft: str
