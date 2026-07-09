import anthropic

from app.schemas import GrantDraftRequest

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are an expert grant writer. You write clear, compelling, \
funder-ready grant proposal drafts based on the organization, project, and \
funder information you're given. Follow any word/page limits and required \
sections implied by the funder's RFP requirements. Write in a professional, \
persuasive, and specific tone — avoid generic filler language."""


def build_user_prompt(request: GrantDraftRequest) -> str:
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
        f"RFP requirements: {funder.rfp_requirements}",
    ]
    if funder.focus_areas:
        lines.append("Focus areas: " + ", ".join(funder.focus_areas))
    if funder.word_or_page_limit:
        lines.append(f"Word/page limit: {funder.word_or_page_limit}")

    return "\n".join(lines)


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

    return next(block.text for block in response.content if block.type == "text")
