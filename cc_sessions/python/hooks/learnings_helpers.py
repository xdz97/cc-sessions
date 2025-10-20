#!/usr/bin/env python3
"""
Learning System Helpers

Provides functions for managing the learning database:
- Topic detection and relevance scoring
- Pattern loading and retrieval
- Learning file I/O operations
"""

# ===== IMPORTS ===== #
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timezone
import json
import re

from shared_state import PROJECT_ROOT

# ===== GLOBALS ===== #
LEARNINGS_DIR = PROJECT_ROOT / "sessions" / "learnings"
INDEX_FILE = LEARNINGS_DIR / "learnings-index.json"

# ===== DATA STRUCTURES ===== #

DEFAULT_TOPICS = {
    "infrastructure": {
        "description": "DevOps, CI/CD, deployments, Docker, K8s, infrastructure",
        "keywords": ["docker", "kubernetes", "k8s", "deploy", "ci/cd", "cicd", "terraform", "ansible", "jenkins", "github actions"],
        "file_patterns": ["*.dockerfile", "Dockerfile", "docker-compose*", "k8s/*", "kubernetes/*", ".github/workflows/*", "*.tf", "*.tfvars"],
        "related_topics": ["security", "api"],
        "last_updated": None
    },
    "sso": {
        "description": "Single Sign-On, OAuth, SAML, authentication flows",
        "keywords": ["oauth", "saml", "jwt", "token", "auth", "sso", "openid", "oidc", "authentication", "login"],
        "file_patterns": ["**/auth/*", "**/sso/*", "**/login/*", "**/oauth/*", "**/saml/*"],
        "related_topics": ["security", "api"],
        "last_updated": None
    },
    "security": {
        "description": "Security vulnerabilities, input validation, crypto, permissions",
        "keywords": ["security", "vulnerability", "xss", "sql injection", "csrf", "cors", "crypto", "encrypt", "hash", "permission", "rbac", "abac"],
        "file_patterns": ["**/security/*", "**/middleware/auth*", "**/permissions/*"],
        "related_topics": ["sso", "api", "database"],
        "last_updated": None
    },
    "api": {
        "description": "REST APIs, GraphQL, endpoints, HTTP, routing",
        "keywords": ["api", "rest", "graphql", "endpoint", "http", "route", "middleware", "fastapi", "express", "flask"],
        "file_patterns": ["**/api/*", "**/routes/*", "**/endpoints/*", "**/controllers/*", "**/handlers/*"],
        "related_topics": ["security", "database"],
        "last_updated": None
    },
    "database": {
        "description": "Database schemas, queries, ORMs, migrations",
        "keywords": ["database", "sql", "postgres", "mysql", "mongo", "orm", "sqlalchemy", "prisma", "typeorm", "migration", "schema"],
        "file_patterns": ["**/models/*", "**/schemas/*", "**/migrations/*", "**/*_model.py", "**/*Model.ts"],
        "related_topics": ["api", "security"],
        "last_updated": None
    },
    "frontend": {
        "description": "UI components, React, Vue, state management",
        "keywords": ["react", "vue", "angular", "component", "ui", "frontend", "redux", "zustand", "state management", "css", "tailwind"],
        "file_patterns": ["**/components/*", "**/views/*", "**/pages/*", "**/*.jsx", "**/*.tsx", "**/*.vue"],
        "related_topics": ["api"],
        "last_updated": None
    },
    "testing": {
        "description": "Unit tests, integration tests, E2E testing",
        "keywords": ["test", "pytest", "jest", "mocha", "vitest", "unittest", "e2e", "integration", "mock"],
        "file_patterns": ["**/tests/*", "**/*_test.py", "**/*.test.ts", "**/*.spec.ts"],
        "related_topics": [],
        "last_updated": None
    }
}

# ===== FUNCTIONS ===== #

def ensure_learnings_structure() -> None:
    """Ensure the learnings directory structure exists"""
    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)

    # Create index if it doesn't exist
    if not INDEX_FILE.exists():
        init_index()

    # Create default topic directories
    index = load_index()
    for topic in index.get("topics", {}).keys():
        topic_dir = LEARNINGS_DIR / topic
        topic_dir.mkdir(exist_ok=True)

        # Create default files if they don't exist
        meta_file = topic_dir / "meta.json"
        if not meta_file.exists():
            topic_data = index["topics"][topic]
            meta_file.write_text(json.dumps(topic_data, indent=2), encoding="utf-8")

        patterns_file = topic_dir / "patterns.json"
        if not patterns_file.exists():
            patterns_file.write_text(json.dumps({
                "successful_patterns": [],
                "anti_patterns": []
            }, indent=2), encoding="utf-8")

        gotchas_file = topic_dir / "gotchas.json"
        if not gotchas_file.exists():
            gotchas_file.write_text(json.dumps({
                "file_specific": {},
                "general_gotchas": []
            }, indent=2), encoding="utf-8")

        history_file = topic_dir / "history.json"
        if not history_file.exists():
            history_file.write_text(json.dumps({
                "tasks_completed": [],
                "common_errors": {}
            }, indent=2), encoding="utf-8")

def init_index() -> None:
    """Initialize the learnings index with default topics"""
    index_data = {
        "topics": DEFAULT_TOPICS,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }
    INDEX_FILE.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

def load_index() -> Dict[str, Any]:
    """Load the learnings index"""
    if not INDEX_FILE.exists():
        init_index()
    return json.loads(INDEX_FILE.read_text(encoding="utf-8"))

def save_index(index: Dict[str, Any]) -> None:
    """Save the learnings index"""
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")

def add_topic(topic_name: str, description: str, keywords: List[str], file_patterns: List[str], related_topics: List[str] = None) -> bool:
    """Add a new topic to the index"""
    index = load_index()

    if topic_name in index["topics"]:
        return False

    index["topics"][topic_name] = {
        "description": description,
        "keywords": keywords,
        "file_patterns": file_patterns,
        "related_topics": related_topics or [],
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

    save_index(index)

    # Create topic directory structure
    topic_dir = LEARNINGS_DIR / topic_name
    topic_dir.mkdir(exist_ok=True)

    # Create empty data files
    (topic_dir / "meta.json").write_text(json.dumps(index["topics"][topic_name], indent=2), encoding="utf-8")
    (topic_dir / "patterns.json").write_text(json.dumps({"successful_patterns": [], "anti_patterns": []}, indent=2), encoding="utf-8")
    (topic_dir / "gotchas.json").write_text(json.dumps({"file_specific": {}, "general_gotchas": []}, indent=2), encoding="utf-8")
    (topic_dir / "history.json").write_text(json.dumps({"tasks_completed": [], "common_errors": {}}, indent=2), encoding="utf-8")

    return True

def detect_relevant_topics(task_content: str, file_paths: List[Path] = None) -> List[str]:
    """
    Detect relevant topics based on task description and file paths

    Returns list of topic names sorted by relevance score
    """
    index = load_index()
    topic_scores = {}

    # Convert content to lowercase for case-insensitive matching
    content_lower = task_content.lower()

    for topic_name, topic_data in index["topics"].items():
        score = 0

        # Check keywords in content
        for keyword in topic_data["keywords"]:
            if keyword.lower() in content_lower:
                score += 2

        # Check file patterns if files provided
        if file_paths:
            for file_path in file_paths:
                path_str = str(file_path).lower()
                for pattern in topic_data["file_patterns"]:
                    # Simple pattern matching (could be enhanced with fnmatch)
                    pattern_parts = pattern.lower().replace("**", "").replace("*", "").split("/")
                    if any(part in path_str for part in pattern_parts if part):
                        score += 3

        if score > 0:
            topic_scores[topic_name] = score

    # Sort by score descending
    sorted_topics = sorted(topic_scores.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, score in sorted_topics]

def load_topic_patterns(topic: str) -> Dict[str, Any]:
    """Load patterns for a specific topic"""
    patterns_file = LEARNINGS_DIR / topic / "patterns.json"
    if not patterns_file.exists():
        return {"successful_patterns": [], "anti_patterns": []}
    return json.loads(patterns_file.read_text(encoding="utf-8"))

def load_topic_gotchas(topic: str) -> Dict[str, Any]:
    """Load gotchas for a specific topic"""
    gotchas_file = LEARNINGS_DIR / topic / "gotchas.json"
    if not gotchas_file.exists():
        return {"file_specific": {}, "general_gotchas": []}
    return json.loads(gotchas_file.read_text(encoding="utf-8"))

def load_topic_history(topic: str) -> Dict[str, Any]:
    """Load history for a specific topic"""
    history_file = LEARNINGS_DIR / topic / "history.json"
    if not history_file.exists():
        return {"tasks_completed": [], "common_errors": {}}
    return json.loads(history_file.read_text(encoding="utf-8"))

def format_learnings_for_protocol(topics: List[str]) -> str:
    """Format learnings into a readable protocol section"""
    if not topics:
        return ""

    output = ["## 📚 Learning Context\n"]
    output.append(f"**Loaded Topics**: {', '.join(topics)}\n")

    for topic in topics:
        patterns = load_topic_patterns(topic)
        gotchas = load_topic_gotchas(topic)

        # Show top 3 successful patterns
        successful = patterns.get("successful_patterns", [])[:3]
        if successful:
            output.append(f"\n### {topic.title()} - Recommended Patterns:\n")
            for pattern in successful:
                output.append(f"- **{pattern['name']}**: {pattern['description']}")
                if pattern.get('example_files'):
                    output.append(f" (see {', '.join(pattern['example_files'])})")
                output.append("\n")

        # Show important gotchas
        file_gotchas = gotchas.get("file_specific", {})
        general_gotchas = gotchas.get("general_gotchas", [])

        if file_gotchas or general_gotchas:
            output.append(f"\n### {topic.title()} - Known Gotchas:\n")

            # File-specific gotchas
            for file_path, issues in list(file_gotchas.items())[:3]:
                for issue in issues[:2]:  # Max 2 per file
                    output.append(f"⚠️ `{file_path}:{issue.get('line_range', '??')}` - {issue['issue']}\n")

            # General gotchas
            for gotcha in general_gotchas[:3]:
                output.append(f"⚠️ {gotcha['issue']}")
                if gotcha.get('solution'):
                    output.append(f" → {gotcha['solution']}")
                output.append("\n")

        # Show anti-patterns to avoid
        anti = patterns.get("anti_patterns", [])[:2]
        if anti:
            output.append(f"\n### {topic.title()} - Anti-Patterns to Avoid:\n")
            for pattern in anti:
                output.append(f"- **{pattern['name']}**: {pattern['problem']}")
                if pattern.get('solution'):
                    output.append(f" → {pattern['solution']}")
                output.append("\n")

    return "".join(output)

def list_all_topics() -> List[str]:
    """List all available learning topics"""
    index = load_index()
    return sorted(index["topics"].keys())

def get_topic_info(topic: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific topic"""
    index = load_index()
    return index["topics"].get(topic)
