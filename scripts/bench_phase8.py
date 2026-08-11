"""Performance benchmarking script for Phase 8a (TextCategorizer) and Phase 8b (SpanCategorizer).

Measures latency impact on preprocessing pipeline. Compares:
1. Legacy: baseline preprocessing without Phase 8 components
2. Phase 8a: with requirement_filter (TextCategorizer)
3. Phase 8a+8b: with requirement_filter + span_categorizer

Generates report: scripts/bench_phase8_results.json
"""

import json
import logging
import statistics
import time
from pathlib import Path
from typing import Any

from src.tokenization.preprocessor import Preprocessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample job descriptions - varying sizes
SAMPLE_JOBS_SMALL = [  # 100-200 tokens
    {
        "id": "small_1",
        "description": """
        Senior Python Developer
        Requirements: 5+ years Python experience, AWS knowledge, Docker experience.
        Nice to have: Django, PostgreSQL, Git.
        """,
    },
    {
        "id": "small_2",
        "description": """
        Frontend Engineer
        Required: React or Vue.js, JavaScript/TypeScript, HTML/CSS.
        Experience with Webpack or Vite preferred.
        """,
    },
    {
        "id": "small_3",
        "description": """
        QA Engineer
        Must have: Selenium, pytest or similar testing framework.
        Experience: 2+ years in automated testing.
        """,
    },
    {
        "id": "small_4",
        "description": """
        DevOps Engineer
        Essential: Kubernetes, Docker, CI/CD pipelines.
        Desired: Terraform, monitoring tools like Prometheus.
        """,
    },
    {
        "id": "small_5",
        "description": """
        Data Analyst
        Required: SQL, Python or R, data visualization.
        Nice to have: Tableau, Google Analytics.
        """,
    },
    {
        "id": "small_6",
        "description": """
        Backend Engineer
        Must have: Java or Go, REST APIs, databases.
        Experience with microservices architecture.
        """,
    },
    {
        "id": "small_7",
        "description": """
        Product Manager
        Required: 3+ years product experience, agile, user research.
        Desired: data analysis, A/B testing, Jira.
        """,
    },
    {
        "id": "small_8",
        "description": """
        Security Engineer
        Essential: OWASP top 10, SSL/TLS, penetration testing.
        Experience: 4+ years cybersecurity or application security.
        """,
    },
    {
        "id": "small_9",
        "description": """
        Cloud Architect
        Required: 6+ years cloud experience (AWS, Azure, GCP).
        Knowledge: infrastructure as code, networking, security.
        """,
    },
    {
        "id": "small_10",
        "description": """
        ML Engineer
        Must have: Python, TensorFlow or PyTorch, statistics.
        Desired: MLOps, model deployment, A/B testing.
        """,
    },
]

SAMPLE_JOBS_MEDIUM = [  # 300-600 tokens each
    {
        "id": "medium_1",
        "description": """
        Senior Full Stack Developer

        We are seeking a Senior Full Stack Developer to join our growing team.

        Required Skills:
        - 5+ years of full-stack development experience
        - Proficiency in React or Vue.js for frontend development
        - Strong backend skills with Node.js, Python, or Java
        - Database design and optimization (SQL and NoSQL)
        - Docker and Kubernetes containerization experience
        - Git and agile development methodologies
        - REST API design and implementation

        Nice to Have:
        - GraphQL experience
        - AWS or GCP cloud platform experience
        - Microservices architecture knowledge
        - CI/CD pipeline implementation
        - TypeScript expertise
        - Performance optimization skills

        Responsibilities:
        - Design and develop scalable web applications
        - Collaborate with product and design teams
        - Mentor junior developers
        - Code reviews and architecture discussions
        """,
    },
    {
        "id": "medium_2",
        "description": """
        Data Scientist

        Join our data team to drive business insights and build predictive models.

        Required:
        - 3+ years as a Data Scientist or Machine Learning Engineer
        - Python proficiency with pandas, NumPy, scikit-learn
        - SQL for data extraction and analysis
        - Statistical analysis and experimental design
        - Machine learning algorithms and frameworks (TensorFlow, PyTorch)
        - Data visualization (Matplotlib, Tableau, or similar)
        - Git version control

        Preferred:
        - Deep learning experience
        - NLP or computer vision background
        - AWS SageMaker or similar MLOps platforms
        - Scala or Java experience
        - Hadoop/Spark for big data
        - Published research or Kaggle competitions

        What You'll Do:
        - Build and train machine learning models
        - Perform exploratory data analysis
        - Deploy models to production
        - Communicate findings to non-technical stakeholders
        """,
    },
    {
        "id": "medium_3",
        "description": """
        Infrastructure Engineer

        Build and maintain our cloud infrastructure.

        Must Have:
        - 4+ years infrastructure engineering experience
        - Kubernetes and Docker expertise
        - Infrastructure as Code (Terraform, Ansible)
        - Linux/Unix system administration
        - AWS, Azure, or GCP experience
        - Networking fundamentals (TCP/IP, DNS, load balancing)
        - Monitoring and observability tools
        - Bash and Python scripting

        Great To Have:
        - Helm charts experience
        - Service mesh knowledge (Istio, Linkerd)
        - Prometheus and Grafana expertise
        - Security hardening and compliance
        - Cost optimization skills
        - ArgoCD or similar GitOps tools

        Your Responsibilities:
        - Design scalable cloud architectures
        - Implement CI/CD pipelines
        - Manage Kubernetes clusters
        - Improve system reliability and performance
        - Automate operational tasks
        """,
    },
    {
        "id": "medium_4",
        "description": """
        Mobile App Developer

        Create amazing iOS and Android applications.

        Required:
        - 3+ years mobile development experience
        - Swift for iOS or Kotlin for Android
        - React Native or Flutter (or both)
        - Mobile UI/UX best practices
        - RESTful API integration
        - Git and version control
        - Testing frameworks (XCTest, Espresso)

        Desired:
        - Cross-platform development experience
        - Push notifications and real-time sync
        - App Store and Google Play publishing
        - Performance optimization
        - Accessibility (WCAG) compliance
        - Firebase experience
        - Continuous integration for mobile

        What You'll Own:
        - Develop new app features
        - Optimize app performance
        - Ensure high code quality
        - Collaborate with design and backend teams
        """,
    },
    {
        "id": "medium_5",
        "description": """
        Site Reliability Engineer

        Ensure our systems run smoothly and scale reliably.

        Must Have:
        - 3+ years SRE or DevOps engineering experience
        - Linux administration expertise
        - Container orchestration (Kubernetes)
        - Scripting in Python, Go, or Bash
        - Database administration (PostgreSQL, MySQL)
        - Monitoring and alerting (Prometheus, DataDog)
        - On-call support experience
        - Incident response and root cause analysis

        Nice To Have:
        - Distributed systems knowledge
        - Cloud platform expertise (AWS, GCP)
        - Network protocols and security
        - Capacity planning and optimization
        - Chaos engineering practices
        - Configuration management tools

        You Will:
        - Maintain and improve system reliability
        - Implement monitoring and observability
        - Automate operational procedures
        - Lead incident response efforts
        - Collaborate with product and engineering teams
        """,
    },
    {
        "id": "medium_6",
        "description": """
        Solutions Architect

        Design enterprise solutions for our customers.

        Required:
        - 5+ years as a Solution Architect or Systems Engineer
        - Deep understanding of cloud architectures (AWS, Azure, GCP)
        - Experience with enterprise software and integrations
        - Knowledge of network design and security
        - Ability to translate business requirements to technical specs
        - Strong communication and presentation skills
        - Experience with infrastructure and application design

        Preferred:
        - Enterprise cloud certifications (AWS Solutions Architect, GCP)
        - Microservices and containerization knowledge
        - Database design (SQL and NoSQL)
        - Cost optimization expertise
        - Compliance and security frameworks (SOC2, HIPAA)
        - Agile and project management experience

        Your Role:
        - Architect customer solutions
        - Lead technical discussions and reviews
        - Collaborate with sales and engineering teams
        - Document technical architectures
        - Provide technical guidance and mentoring
        """,
    },
    {
        "id": "medium_7",
        "description": """
        Compliance Engineer

        Help us maintain security and compliance standards.

        Must Have:
        - 3+ years in compliance, security, or risk management
        - Knowledge of compliance frameworks (SOC2, ISO27001, GDPR)
        - Experience with security audits and assessments
        - Understanding of data protection and privacy regulations
        - Risk management and threat modeling skills
        - Documentation and process improvement
        - Technical understanding of cloud platforms

        Desired:
        - Security certifications (CISSP, CISM, CCSK)
        - Incident response experience
        - Penetration testing knowledge
        - Third-party risk management
        - Automation and scripting skills
        - ISMS development and implementation

        Responsibilities:
        - Monitor regulatory compliance
        - Conduct security assessments
        - Develop policies and procedures
        - Lead compliance initiatives
        - Work with cross-functional teams
        """,
    },
    {
        "id": "medium_8",
        "description": """
        Platform Engineer

        Build developer platforms and tools.

        Required:
        - 4+ years platform or infrastructure engineering
        - Strong programming skills (Go, Rust, or similar)
        - Kubernetes and container expertise
        - API design and implementation
        - Distributed systems understanding
        - Software engineering best practices
        - Git and version control

        Nice To Have:
        - Service mesh architecture
        - Event-driven architecture
        - Database design for scale
        - CLI tool development
        - Developer experience optimization
        - Open source contributions

        You Will:
        - Design and build internal developer platforms
        - Create self-service capabilities for teams
        - Improve developer productivity
        - Maintain platform reliability
        - Mentor other engineers
        """,
    },
    {
        "id": "medium_9",
        "description": """
        Analytics Engineer

        Bridge data and analytics teams.

        Required:
        - 2+ years as Analytics Engineer or Data Analyst
        - Advanced SQL skills for complex queries
        - Proficiency in dbt (data build tool) or similar
        - Data warehouse knowledge (Snowflake, BigQuery)
        - Python or R for data transformation
        - Git and version control practices
        - Experience with BI tools (Looker, Tableau)

        Preferred:
        - Dimensional modeling and star schema design
        - Data quality frameworks
        - ETL/ELT pipeline development
        - A/B testing and experimentation
        - Statistical analysis
        - Cloud data platform experience

        Responsibilities:
        - Build data models and pipelines
        - Optimize data warehouse performance
        - Support analytics and BI team
        - Create data documentation
        - Monitor data quality and freshness
        """,
    },
    {
        "id": "medium_10",
        "description": """
        Engineering Manager

        Lead and develop engineering teams.

        Must Have:
        - 3+ years engineering management experience
        - Track record of building and scaling teams
        - Technical background (software engineering)
        - Strong communication and people skills
        - Strategic thinking and planning abilities
        - Project management experience
        - Mentoring and coaching skills

        Nice To Have:
        - Multiple team or organization management
        - Hiring and retention expertise
        - Agile and lean methodologies
        - Conflict resolution experience
        - Budget and resource planning
        - Cross-functional collaboration

        Your Responsibilities:
        - Manage engineering team performance
        - Develop team members' careers
        - Define team goals and strategies
        - Ensure delivery of projects
        - Foster team culture and collaboration
        """,
    },
]

# Combine all samples (using only small + medium to avoid long lines in source)
ALL_JOBS = SAMPLE_JOBS_SMALL + SAMPLE_JOBS_MEDIUM

# Using 20 jobs (10 small, 10 medium) for representative benchmark
assert len(ALL_JOBS) == 20, f"Expected 20 jobs, got {len(ALL_JOBS)}"


def benchmark_pipeline(
    jobs: list[dict[str, Any]],
    extract_requirements: bool = False,
    preserve_requirement_spans: bool = False,
) -> dict[str, Any]:
    """Run benchmark on a pipeline configuration.

    Args:
        jobs: List of job dictionaries with 'description' field
        extract_requirements: Whether to enable requirement_filter
        preserve_requirement_spans: Whether to enable span_categorizer

    Returns:
        Dictionary with timing metrics
    """
    preprocessor = Preprocessor(
        extract_requirements=extract_requirements,
        preserve_requirement_spans=preserve_requirement_spans,
    )

    timings: dict[str, list[float]] = {
        "nlp_pipeline": [],
        "total": [],
    }

    for job in jobs:
        text = job["description"]

        # Time NLP pipeline
        start = time.time()
        _ = preprocessor.nlp(text)  # type: ignore[misc]
        elapsed_ms = (time.time() - start) * 1000
        timings["nlp_pipeline"].append(elapsed_ms)
        timings["total"].append(elapsed_ms)

    return {
        "count": len(jobs),
        "mean_ms": statistics.mean(timings["total"]),
        "median_ms": statistics.median(timings["total"]),
        "min_ms": min(timings["total"]),
        "max_ms": max(timings["total"]),
        "p95_ms": sorted(timings["total"])[int(len(timings["total"]) * 0.95)],
        "p99_ms": sorted(timings["total"])[int(len(timings["total"]) * 0.99)],
        "stdev_ms": statistics.stdev(timings["total"]) if len(timings["total"]) > 1 else 0,
    }


def main() -> int:
    """Run benchmarks and generate report."""
    logger.info("Starting Phase 8 performance benchmarking...")
    logger.info(f"Sample size: {len(ALL_JOBS)} jobs")

    # Run benchmarks
    logger.info("\n1. Benchmarking legacy pipeline (no Phase 8 components)...")
    legacy_results = benchmark_pipeline(ALL_JOBS, extract_requirements=False, preserve_requirement_spans=False)

    logger.info("2. Benchmarking Phase 8a only (requirement_filter)...")
    phase8a_results = benchmark_pipeline(ALL_JOBS, extract_requirements=True, preserve_requirement_spans=False)

    logger.info("3. Benchmarking Phase 8a+8b (both components)...")
    phase8b_results = benchmark_pipeline(ALL_JOBS, extract_requirements=True, preserve_requirement_spans=True)

    # Calculate overheads
    overhead_8a_ms = phase8a_results["mean_ms"] - legacy_results["mean_ms"]
    overhead_8b_ms = phase8b_results["mean_ms"] - phase8a_results["mean_ms"]
    total_overhead_ms = phase8b_results["mean_ms"] - legacy_results["mean_ms"]

    # Compile report
    report = {
        "metadata": {
            "timestamp": time.time(),
            "sample_count": len(ALL_JOBS),
            "job_breakdown": {
                "small_100_200_tokens": len(SAMPLE_JOBS_SMALL),
                "medium_300_600_tokens": len(SAMPLE_JOBS_MEDIUM),
            },
        },
        "results": {
            "legacy_baseline": legacy_results,
            "phase_8a_only": phase8a_results,
            "phase_8a_8b_combined": phase8b_results,
        },
        "overhead_analysis": {
            "phase_8a_overhead_ms": overhead_8a_ms,
            "phase_8b_overhead_ms": overhead_8b_ms,
            "total_overhead_ms": total_overhead_ms,
            "target_met": total_overhead_ms < 150,
            "target_threshold_ms": 150,
        },
    }

    # Log results
    logger.info("\n" + "=" * 70)
    logger.info("BENCHMARK RESULTS")
    logger.info("=" * 70)

    logger.info("\nLegacy Baseline (no Phase 8):")
    for key, value in legacy_results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2f}ms")
        else:
            logger.info(f"  {key}: {value}")

    logger.info("\nPhase 8a Only (requirement_filter):")
    for key, value in phase8a_results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2f}ms")
        else:
            logger.info(f"  {key}: {value}")

    logger.info("\nPhase 8a+8b Combined (requirement_filter + span_categorizer):")
    for key, value in phase8b_results.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.2f}ms")
        else:
            logger.info(f"  {key}: {value}")

    logger.info("\n" + "=" * 70)
    logger.info("OVERHEAD ANALYSIS")
    logger.info("=" * 70)

    legacy_mean = legacy_results["mean_ms"]
    phase8a_mean = phase8a_results["mean_ms"]
    phase8b_mean = phase8b_results["mean_ms"]

    pct_8a = overhead_8a_ms / legacy_mean * 100
    pct_8b = overhead_8b_ms / phase8a_mean * 100
    pct_total = total_overhead_ms / legacy_mean * 100

    logger.info(f"Phase 8a overhead: +{overhead_8a_ms:.2f}ms (+{pct_8a:.1f}%)")
    logger.info(f"Phase 8b overhead: +{overhead_8b_ms:.2f}ms ({pct_8b:.1f}%)")
    logger.info(f"Total overhead: +{total_overhead_ms:.2f}ms (+{pct_total:.1f}%)")
    logger.info("Target threshold: <150ms")

    target_met = report["overhead_analysis"]["target_met"]  # type: ignore[index]
    status = "✓ YES" if target_met else "✗ NO"
    logger.info(f"Target met: {status}")

    # Save report
    output_file = Path("scripts/bench_phase8_results.json")
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"\nResults saved to: {output_file}")

    # Return exit code based on target
    target_met = report["overhead_analysis"]["target_met"]  # type: ignore[index]
    if not target_met:
        actual_ms = phase8b_mean
        logger.warning(f"\n⚠ Performance target NOT met: {actual_ms:.2f}ms > 150ms threshold")
        return 1

    logger.info("\n✓ Performance target MET")
    return 0


if __name__ == "__main__":
    exit(main())
