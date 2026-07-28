"""Technology keywords for NLP entity extraction.

Organized by category for easy maintenance and discoverability.
Includes 44 baseline keywords + 42 Phase 2 additions (86 total).
"""

TECH_KEYWORDS = {
    # Programming Languages (13)
    "languages": {
        "python",
        "javascript",
        "typescript",
        "java",
        "c#",
        "csharp",
        "go",
        "rust",
        "php",
        "ruby",
        "c++",
        "scala",
        "kotlin",
    },
    # Web Frameworks & Libraries (13)
    "web": {
        "react",
        "vue",
        "angular",
        "node",
        "express",
        "django",
        "flask",
        "fastapi",
        "next",
        "nextjs",
        "nuxt",
        "svelte",
        "astro",
    },
    # Cloud & Infrastructure (15)
    "infrastructure": {
        "aws",
        "gcp",
        "azure",
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "helm",
        "ansible",
        "consul",
        "vault",
        "prometheus",
        "docker-compose",
        "podman",
        "buildah",
    },
    # Databases (13)
    "databases": {
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "cassandra",
        "elasticsearch",
        "kafka",
        "dynamodb",
        "firestore",
        "snowflake",
        "bigquery",
        "duckdb",
        "cockroachdb",
    },
    # Hardware/FPGA/Embedded (18) - CRITICAL for ATS domain
    "hardware": {
        "verilog",
        "systemverilog",
        "asic",
        "fpga",
        "arm",
        "rtl",
        "dft",
        "lint",
        "ddr",
        "spi",
        "i2c",
        "uart",
        "can",
        "esd",
        "lef",
        "def",
        "gds",
        "matlab",
    },
    # ML/AI Frameworks (20)
    "ml_ai": {
        "tensorflow",
        "pytorch",
        "sklearn",
        "jax",
        "huggingface",
        "transformers",
        "onnx",
        "keras",
        "xgboost",
        "lightgbm",
        "catboost",
        "mlflow",
        "wandb",
        "opencv",
        "yolo",
        "spacy",
        "bert",
        "gpt",
        "llm",
        "timm",
    },
    # DevOps & Tools (15)
    "tools": {
        "jira",
        "confluence",
        "git",
        "gitlab",
        "github",
        "bitbucket",
        "circleci",
        "travis",
        "jenkins",
        "airflow",
        "prefect",
        "rest",
        "grpc",
        "graphql",
        "sql",
    },
    # Methodologies & Practices (8)
    "methodologies": {
        "agile",
        "scrum",
        "kanban",
        "tdd",
        "bdd",
        "ddd",
        "lean",
        "xp",
    },
    # Robotics & Emerging (5)
    "robotics": {
        "ros",
        "ros2",
        "gazebo",
        "moveit",
        "webots",
    },
    # Other Critical Tools (8)
    "other": {
        "protobuf",
        "json",
        "xml",
        "yaml",
        "kubeflow",
        "ray",
        "cadence",
        "synopsys",
    },
}


def get_all_keywords() -> set[str]:
    """Get flattened set of all keywords across categories.

    Returns:
        Set of all technology keywords (86 total)
    """
    all_kw = set()
    for category_keywords in TECH_KEYWORDS.values():
        all_kw.update(category_keywords)
    return all_kw


def get_keywords_by_category(category: str) -> set[str]:
    """Get keywords for specific category.

    Args:
        category: One of languages, web, infrastructure, databases,
                 hardware, ml_ai, tools, methodologies, robotics, other

    Returns:
        Set of keywords in that category, or empty set if not found
    """
    return TECH_KEYWORDS.get(category, set())


def get_categories() -> list[str]:
    """Get list of keyword categories.

    Returns:
        List of category names
    """
    return list(TECH_KEYWORDS.keys())
