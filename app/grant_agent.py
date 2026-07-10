import base64

import anthropic

from app.schemas import GrantDraftRequest

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are an expert grant writer. You write clear, compelling, \
funder-ready grant proposal drafts based on the organization, project, and \
funder information you're given. Follow any word/page limits and required \
sections implied by the funder's RFP requirements — read any attached RFP \
or supporting documents carefully before drafting. Write in a professional, \
persuasive, and specific tone — avoid generic filler language."""


def build_user_prompt(request: GrantDraftRequest, has_documents: bool = False) -> str:
    org = request.organization
    project = request.project
    funder = request.funder

    lines = [
        "Write a full grant proposal draft using the following information.",
        "",
        "## Organization",
        f"Name: {org.name}",
        f"Mission: {org.mission}",
    ]
    if org.ein:
        lines.append(f"EIN: {org.ein}")
    if org.years_operating is not None:
        lines.append(f"Years operating: {org.years_operating}")
    if org.past_grants:
        lines.append("Past grants received:")
        lines.extend(f"- {g}" for g in org.past_grants)

    lines += [
        "",
        "## Project",
        f"Title: {project.title}",
        f"Description: {project.description}",
    ]
    if project.target_population:
        lines.append(f"Target population: {project.target_population}")
    if project.goals:
        lines.append("Goals:")
        lines.extend(f"- {g}" for g in project.goals)
    if project.timeline:
        lines.append(f"Timeline: {project.timeline}")
    if project.requested_amount is not None:
        lines.append(f"Requested amount: ${project.requested_amount:,.2f}")
    if project.budget_notes:
        lines.append(f"Budget notes: {project.budget_notes}")

    lines += [
        "",
        "## Funder",
        f"Name: {funder.name}",
    ]
    if funder.rfp_requirements:
        lines.append(f"RFP requirements: {funder.rfp_requirements}")
    elif has_documents:
        lines.append("RFP requirements: see the attached document(s) above.")
    if funder.focus_areas:
        lines.append("Focus areas: " + ", ".join(funder.focus_areas))
    if funder.word_or_page_limit:
        lines.append(f"Word/page limit: {funder.word_or_page_limit}")

    return "\n".join(lines)


def _extract_text(response: anthropic.types.Message) -> str:
    return next(block.text for block in response.content if block.type == "text")


def generate_grant_draft(request: GrantDraftRequest) -> str:
    client = anthropic.Anthropic()

    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": build_user_prompt(request)}],
    ) as stream:
        response = stream.get_final_message()

    return _extract_text(response)


def _pdf_block(pdf_bytes: bytes, title: str | None = None) -> dict:
    block = {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": base64.standard_b64encode(pdf_bytes).decode("utf-8"),
        },
    }
    if title:
        block["title"] = title
    return block


def generate_grant_draft_with_documents(
    request: GrantDraftRequest,
    rfp_pdf: bytes | None = None,
    supporting_pdfs: list[tuple[str, bytes]] | None = None,
) -> str:
    """Same as generate_grant_draft, but with PDFs (RFP and/or supporting docs)
    attached directly to the request instead of requiring pasted-in text."""
    supporting_pdfs = supporting_pdfs or []
    client = anthropic.Anthropic()

    content: list[dict] = []
    if rfp_pdf:
        content.append(_pdf_block(rfp_pdf, title="RFP"))
    for filename, pdf_bytes in supporting_pdfs:
        content.append(_pdf_block(pdf_bytes, title=filename))

    has_documents = bool(content)
    content.append(
        {"type": "text", "text": build_user_prompt(request, has_documents=has_documents)}
    )

    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": content}],
    ) as stream:
        response = stream.get_final_message()

    return _extract_text(response)
