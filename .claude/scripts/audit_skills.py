#!/usr/bin/env python
"""Audit extracted skills for inappropriate content."""

import json
from collections import defaultdict
from pathlib import Path


def categorize_skill(skill: str) -> str:
    """Categorize skill by type."""
    skill_lower = skill.lower()

    # Tech skills
    tech_keywords = {
        "python",
        "java",
        "javascript",
        "rust",
        "go",
        "c#",
        "c++",
        "react",
        "angular",
        "vue",
        "django",
        "flask",
        "spring",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "postgresql",
        "mongodb",
        "redis",
        "elasticsearch",
        "tensorflow",
        "pytorch",
        "sklearn",
        "git",
        "github",
        "gitlab",
        "jira",
    }
    if any(kw in skill_lower for kw in tech_keywords):
        return "TECH"

    # Soft skills / methods
    soft_keywords = {
        "communication",
        "leadership",
        "problem solving",
        "team",
        "agile",
        "scrum",
        "kanban",
        "project management",
        "mentoring",
        "collaboration",
        "organization",
    }
    if any(kw in skill_lower for kw in soft_keywords):
        return "SOFT"

    # Suspicious patterns (potential junk)
    suspicious = {
        "and",
        "or",
        "with",
        "for",
        "able",
        "skills",
        "experience",
        "years",
        "years of",
        "work",
        "knowledge",
        "understanding",
        "familiarity",
        "required",
        "preferred",
        "able to",
    }
    if any(kw in skill_lower for kw in suspicious):
        return "SUSPICIOUS"

    # Fragments / incomplete
    if len(skill) < 3:
        return "FRAGMENT"

    # Generic words
    generic = {
        "you",
        "your",
        "we",
        "our",
        "a",
        "the",
        "is",
        "be",
        "are",
        "was",
        "were",
        "been",
        "have",
        "has",
        "do",
        "does",
    }
    if skill_lower in generic:
        return "GENERIC"

    return "VALID"


def analyze_skills():
    """Analyze skills in preprocessed jobs."""
    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print(f"❌ File not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print("=" * 100)
    print("SKILLS AUDIT: Inappropriate Chunks Analysis")
    print("=" * 100)
    print()

    issues_by_type = defaultdict(list)
    all_skills_by_category = defaultdict(list)
    job_skill_counts = []

    for job_idx, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown")[:50]
        skills = job.get("skills", [])
        chunks = job.get("chunks", [])

        job_skill_counts.append((job_idx, title, len(skills)))

        for skill in skills:
            category = categorize_skill(skill)
            all_skills_by_category[category].append(skill)

            if category in ["SUSPICIOUS", "FRAGMENT", "GENERIC"]:
                # Find which chunk contains this skill
                chunk_source = None
                for chunk in chunks:
                    if skill.lower() in chunk.lower():
                        chunk_source = chunk[:150]
                        break

                issues_by_type[category].append(
                    {"job_idx": job_idx, "title": title, "skill": skill, "chunk_preview": chunk_source or "NOT FOUND"}
                )

    # Print by category
    print(f"\n📊 SKILLS BREAKDOWN ({sum(len(v) for v in all_skills_by_category.values())} total)")
    print("-" * 100)
    for category in ["VALID", "TECH", "SOFT", "SUSPICIOUS", "FRAGMENT", "GENERIC"]:
        count = len(all_skills_by_category[category])
        if count > 0:
            pct = count / sum(len(v) for v in all_skills_by_category.values()) * 100
            print(f"{category:12} {count:4} ({pct:5.1f}%)")

    # Print job distribution
    print("\n\n📈 SKILLS PER JOB")
    print("-" * 100)
    for idx, title, count in job_skill_counts:
        print(f"Job {idx}: {title:45} {count:3} skills")

    # Print issues found
    if issues_by_type:
        print("\n\n⚠️  INAPPROPRIATE SKILLS FOUND")
        print("-" * 100)

        for category in ["SUSPICIOUS", "FRAGMENT", "GENERIC"]:
            if category not in issues_by_type:
                continue

            issues = issues_by_type[category]
            print(f"\n{category} ({len(issues)} issues):")
            print()

            for issue in issues[:5]:  # Show top 5
                print(f"Job {issue['job_idx']}: {issue['title']}")
                print(f"  Skill: '{issue['skill']}'")
                print(f"  From: {issue['chunk_preview']}...")
                print()

            if len(issues) > 5:
                print(f"  ... and {len(issues) - 5} more {category} issues")
                print()

    # Summary
    print("\n\n📋 RECOMMENDATIONS")
    print("-" * 100)

    if issues_by_type.get("SUSPICIOUS"):
        print(f"✗ {len(issues_by_type['SUSPICIOUS'])} SUSPICIOUS skills")
        print("  → Expand boilerplate_keywords with phrases like 'able to', 'with', 'and'")
        print()

    if issues_by_type.get("FRAGMENT"):
        print(f"✗ {len(issues_by_type['FRAGMENT'])} FRAGMENT skills (< 3 chars)")
        print("  → Filter: len(skill) < 3 before adding to skills list")
        print()

    if issues_by_type.get("GENERIC"):
        print(f"✗ {len(issues_by_type['GENERIC'])} GENERIC skills")
        print("  → Expand boilerplate_keywords with common words")
        print()

    if not any(issues_by_type.values()):
        print("✅ No inappropriate skills found!")
        print()


if __name__ == "__main__":
    analyze_skills()
