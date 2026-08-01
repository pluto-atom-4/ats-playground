"""Soft skills taxonomy for NLP skill extraction."""

SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "collaboration", "problem-solving",
    "critical thinking", "creative", "adaptability", "flexibility", "analytical",
    "organizational", "time management", "attention to detail", "customer service",
    "interpersonal", "negotiation", "listening", "presentation", "public speaking",
    "written communication", "oral communication", "multitasking", "conflict resolution",
    "project management", "decision making", "mentoring", "coaching", "training",
    "strategic thinking", "business acumen", "emotional intelligence", "initiative",
    "self-motivated", "reliable", "trustworthy", "honest", "integrity",
    "professional", "responsible", "accountable", "independent", "self-sufficient",
}


def get_all_soft_skills() -> set[str]:
    """Get all soft skills."""
    return SOFT_SKILLS
