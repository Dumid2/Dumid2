from pathlib import Path

ORG_PROFILE_DIR = Path(__file__).resolve().parent / "org_profile"
ORG_NAME = "GOODProjects, Inc."


def load_org_profile() -> str:
    """Concatenate every reference file in app/org_profile/ into one block,
    used as fixed grounding context for every grant draft. Add new files to
    that directory (any filename) to extend what the agent knows — no code
    changes needed."""
    sections = []
    for path in sorted(ORG_PROFILE_DIR.glob("*.md")):
        sections.append(f"<!-- source: {path.name} -->\n{path.read_text()}")
    return "\n\n---\n\n".join(sections)
