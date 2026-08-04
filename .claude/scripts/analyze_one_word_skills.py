#!/usr/bin/env python
"""Analyze one-word skills to identify overly generic entries."""

import json
from collections import defaultdict
from pathlib import Path


def categorize_word(word: str) -> str:
    """Categorize a one-word skill."""
    word_lower = word.lower()

    # Known legitimate tech terms
    tech_terms = {
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
        "fastapi",
        "aws",
        "azure",
        "gcp",
        "kubernetes",
        "docker",
        "postgres",
        "mongodb",
        "redis",
        "elasticsearch",
        "kafka",
        "git",
        "terraform",
        "ansible",
        "jenkins",
        "tensorflow",
        "pytorch",
        "scikit-learn",
        "pandas",
        "numpy",
        "agile",
        "scrum",
        "jira",
        "sql",
        "html",
        "css",
        "xml",
        "json",
        "yaml",
        "protobuf",
        "graphql",
        "rest",
        "grpc",
    }

    # Generic words that shouldn't be skills
    generic_words = {
        # Verbs
        "planning",
        "management",
        "development",
        "testing",
        "training",
        "support",
        "implementation",
        "analysis",
        "design",
        "engineering",
        "operations",
        "maintenance",
        "monitoring",
        "deployment",
        "debugging",
        "optimization",
        "coordination",
        "collaboration",
        "communication",
        # Nouns (non-tech)
        "experience",
        "knowledge",
        "understanding",
        "ability",
        "skill",
        "leadership",
        "teamwork",
        "work",
        "team",
        "project",
        "system",
        "process",
        "organization",
        "company",
        "business",
        "industry",
        "environment",
        "application",
        "platform",
        "solution",
        "technology",
        "framework",
        "library",
        "tool",
        "service",
        "product",
        "requirement",
        "documentation",
        "specification",
        "architecture",
        # Adjectives
        "strong",
        "excellent",
        "good",
        "high",
        "low",
        "large",
        "small",
        "complex",
        "simple",
        "advanced",
        "basic",
        "modern",
        "legacy",
        "distributed",
        "scalable",
        "reliable",
        "secure",
        "efficient",
        "effective",
        "professional",
        "technical",
        "general",
        "specific",
        # Abstract
        "concept",
        "principle",
        "practice",
        "method",
        "approach",
        "strategy",
        "pattern",
        "standard",
        "protocol",
        "interface",
    }

    if word_lower in tech_terms:
        return "TECH"
    elif word_lower in generic_words:
        return "GENERIC"
    else:
        return "UNKNOWN"


def main():
    """Analyze one-word skills."""
    jobs_file = Path("data/extracted_jobs/preprocessed_jobs.json")
    if not jobs_file.exists():
        print(f"❌ File not found: {jobs_file}")
        return

    with open(jobs_file) as f:
        jobs = json.load(f)

    print("=" * 100)
    print("ONE-WORD SKILLS ANALYSIS")
    print("=" * 100)
    print()

    all_one_word = defaultdict(list)
    generic_by_job = defaultdict(list)
    total_skills = 0
    total_one_word = 0
    total_generic = 0

    for job_idx, job in enumerate(jobs, 1):
        title = job.get("title", "Unknown")[:50]
        skills = job.get("skills", [])
        total_skills += len(skills)

        for skill in skills:
            if " " not in skill:  # One-word skill
                total_one_word += 1
                category = categorize_word(skill)
                all_one_word[skill].append((job_idx, title, category))

                if category == "GENERIC":
                    total_generic += 1
                    generic_by_job[job_idx].append((skill, title))

    print("📊 SUMMARY")
    print("-" * 100)
    print(f"Total skills: {total_skills}")
    print(f"One-word skills: {total_one_word} ({total_one_word / total_skills * 100:.1f}%)")
    print(f"Generic one-word: {total_generic} ({total_generic / total_one_word * 100:.1f}%)")
    print()

    print(f"🔴 GENERIC ONE-WORD SKILLS ({total_generic} total)")
    print("-" * 100)

    generic_words_list = {}
    for skill, occurrences in sorted(all_one_word.items()):
        if all(cat == "GENERIC" for _, _, cat in occurrences):
            generic_words_list[skill] = len(occurrences)

    for skill in sorted(generic_words_list.keys(), key=lambda s: generic_words_list[s], reverse=True):
        count = generic_words_list[skill]
        print(f"• {skill:20} appears in {count} jobs")

    print()
    print(f"✅ LEGITIMATE ONE-WORD SKILLS ({total_one_word - total_generic})")
    print("-" * 100)

    tech_words_list = {}
    for skill, occurrences in sorted(all_one_word.items()):
        if all(cat == "TECH" for _, _, cat in occurrences):
            tech_words_list[skill] = len(occurrences)

    for skill in sorted(tech_words_list.keys(), key=lambda s: tech_words_list[s], reverse=True):
        count = tech_words_list[skill]
        print(f"• {skill:20} appears in {count} jobs")

    print()
    print("❓ UNKNOWN ONE-WORD SKILLS")
    print("-" * 100)

    unknown_words_list = {}
    for skill, occurrences in sorted(all_one_word.items()):
        if any(cat == "UNKNOWN" for _, _, cat in occurrences):
            unknown_words_list[skill] = len(occurrences)

    for skill in sorted(unknown_words_list.keys(), key=lambda s: unknown_words_list[s], reverse=True)[:20]:
        count = unknown_words_list[skill]
        print(f"• {skill:20} appears in {count} jobs")

    if len(unknown_words_list) > 20:
        print(f"... and {len(unknown_words_list) - 20} more")

    print()
    print("📋 RECOMMENDATIONS")
    print("-" * 100)
    print(f"✗ Filter {total_generic} generic one-word skills")
    print(f"✓ Keep {total_one_word - total_generic} legitimate tech/domain skills")
    print()
    print("Generic one-word skills to add to filter:")
    for skill in sorted(generic_words_list.keys()):
        print(f'    "{skill}",')


if __name__ == "__main__":
    main()
