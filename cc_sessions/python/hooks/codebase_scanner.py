#!/usr/bin/env python3
"""
Codebase Scanner

Analyzes existing codebase to discover patterns, tech stack, and potential gotchas.
Pre-populates the learning database with discovered information.
"""

# ===== IMPORTS ===== #
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import Counter, defaultdict
import json
import re

from shared_state import PROJECT_ROOT

# ===== GLOBALS ===== #

# File patterns for tech detection
TECH_SIGNATURES = {
    "infrastructure": {
        "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
        "kubernetes": ["k8s/", "kubernetes/", "*.yaml", "*.yml"],
        "terraform": ["*.tf", "*.tfvars", "terraform/"],
        "ansible": ["ansible/", "playbook.yml", "*.ansible.yml"],
        "ci_cd": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/"],
    },
    "sso": {
        "oauth": ["oauth", "OAuth", "auth/oauth", "oauth2"],
        "saml": ["saml", "SAML", "auth/saml"],
        "jwt": ["jwt", "JWT", "jsonwebtoken"],
        "oidc": ["oidc", "openid", "OpenID"],
    },
    "security": {
        "crypto": ["crypto", "encryption", "bcrypt", "argon2", "pbkdf2"],
        "auth": ["auth", "authentication", "authorize", "permission", "rbac"],
        "validation": ["validator", "sanitize", "validate"],
    },
    "api": {
        "rest": ["api/", "routes/", "endpoints/", "controllers/", "handlers/"],
        "graphql": ["graphql", "schema.graphql", "resolvers"],
        "fastapi": ["fastapi", "FastAPI"],
        "express": ["express", "app.use"],
        "flask": ["flask", "Flask", "@app.route"],
    },
    "database": {
        "postgres": ["psycopg2", "postgresql", "postgres"],
        "mysql": ["mysql", "pymysql", "MySQL"],
        "mongodb": ["mongo", "mongodb", "pymongo"],
        "sqlalchemy": ["sqlalchemy", "SQLAlchemy", "Base.metadata"],
        "prisma": ["prisma", "@prisma/client", "schema.prisma"],
        "typeorm": ["typeorm", "TypeORM", "@Entity"],
    },
    "frontend": {
        "react": ["react", "React", "useState", "useEffect", ".jsx", ".tsx"],
        "vue": ["vue", "Vue", ".vue", "createApp"],
        "angular": ["angular", "@angular/", "ng-"],
        "svelte": ["svelte", "Svelte"],
    },
    "testing": {
        "pytest": ["pytest", "test_*.py", "conftest.py"],
        "jest": ["jest", "*.test.js", "*.test.ts", "*.spec.js"],
        "mocha": ["mocha", "describe(", "it("],
        "vitest": ["vitest", "*.test.ts"],
    }
}

# Common patterns to detect
PATTERN_SIGNATURES = {
    "error_handling": [
        r"try\s*{",
        r"try:",
        r"catch\s*\(",
        r"except\s+\w+",
        r"\.catch\(",
        r"throw new",
        r"raise\s+\w+",
    ],
    "async_patterns": [
        r"async\s+def\s+\w+",
        r"async\s+function\s+\w+",
        r"await\s+",
        r"asyncio\.",
        r"Promise\.",
        r"\.then\(",
    ],
    "validation": [
        r"validate\w*\(",
        r"sanitize\w*\(",
        r"if\s+not\s+\w+:",
        r"if\s*\(\s*!\w+",
        r"assert\s+",
        r"\.required\(\)",
    ],
    "authentication": [
        r"@login_required",
        r"@requires_auth",
        r"authenticate\(",
        r"verify_token",
        r"check_permission",
        r"is_authenticated",
    ],
    "database_queries": [
        r"\.query\(",
        r"\.filter\(",
        r"SELECT\s+",
        r"INSERT\s+INTO",
        r"UPDATE\s+",
        r"DELETE\s+FROM",
        r"\.find\(",
        r"\.findOne\(",
    ],
    "configuration": [
        r"os\.environ\.",
        r"process\.env\.",
        r"config\.",
        r"settings\.",
        r"\.env",
        r"CONFIG\[",
    ]
}

# ===== FUNCTIONS ===== #

def scan_codebase(max_files: int = 500) -> Dict[str, Any]:
    """
    Scan the codebase and return discovered patterns and tech stack

    Args:
        max_files: Maximum number of files to scan (prevent huge scans)

    Returns:
        Dictionary with discovered information
    """
    results = {
        "tech_stack": defaultdict(list),
        "patterns": defaultdict(int),
        "file_statistics": {},
        "potential_gotchas": [],
        "architectural_insights": []
    }

    # Determine which directories to scan
    scan_dirs = get_scan_directories()

    files_scanned = 0
    total_lines = 0

    for scan_dir in scan_dirs:
        if files_scanned >= max_files:
            break

        for file_path in scan_dir.rglob("*"):
            if files_scanned >= max_files:
                break

            if not file_path.is_file():
                continue

            # Skip certain files/directories
            if should_skip_file(file_path):
                continue

            files_scanned += 1

            # Detect tech stack from file
            detect_tech_from_file(file_path, results["tech_stack"])

            # Analyze file content if it's a code file
            if is_code_file(file_path):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    lines = content.splitlines()
                    total_lines += len(lines)

                    # Detect patterns
                    detect_patterns(content, results["patterns"])

                    # Look for potential gotchas
                    gotchas = detect_gotchas(file_path, content)
                    results["potential_gotchas"].extend(gotchas)

                except Exception:
                    pass  # Skip files that can't be read

    results["file_statistics"] = {
        "files_scanned": files_scanned,
        "total_lines": total_lines,
        "avg_lines_per_file": total_lines // files_scanned if files_scanned > 0 else 0
    }

    # Analyze architecture
    results["architectural_insights"] = analyze_architecture(results["tech_stack"])

    return results

def get_scan_directories() -> List[Path]:
    """Get list of directories to scan, excluding common non-code dirs"""
    exclude_dirs = {
        "node_modules", "venv", ".venv", "env", ".env", "dist", "build",
        "__pycache__", ".git", ".pytest_cache", "coverage", ".next",
        "target", "out", ".cache", "vendor", ".tox"
    }

    scan_dirs = []
    for item in PROJECT_ROOT.iterdir():
        if item.is_dir() and item.name not in exclude_dirs and not item.name.startswith('.'):
            scan_dirs.append(item)

    return scan_dirs

def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped during scan"""
    skip_patterns = [
        ".min.js", ".min.css", ".map", ".lock", ".log",
        "package-lock.json", "yarn.lock", "poetry.lock",
        ".pyc", ".pyo", ".so", ".dylib", ".dll"
    ]

    # Skip by suffix
    for pattern in skip_patterns:
        if str(file_path).endswith(pattern):
            return True

    # Skip hidden files
    if file_path.name.startswith('.'):
        return True

    # Skip large files (> 1MB)
    try:
        if file_path.stat().st_size > 1_000_000:
            return True
    except:
        return True

    return False

def is_code_file(file_path: Path) -> bool:
    """Check if file is a code file worth analyzing"""
    code_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.sh', '.bash', '.zsh', '.yaml', '.yml',
        '.json', '.toml', '.ini', '.conf', '.sql'
    }
    return file_path.suffix in code_extensions

def detect_tech_from_file(file_path: Path, tech_stack: Dict[str, List[str]]) -> None:
    """Detect technology from file path and name"""
    file_str = str(file_path).lower()
    file_name = file_path.name.lower()

    for topic, tech_patterns in TECH_SIGNATURES.items():
        for tech_name, patterns in tech_patterns.items():
            for pattern in patterns:
                if pattern.lower() in file_str or pattern.lower() == file_name:
                    if tech_name not in tech_stack[topic]:
                        tech_stack[topic].append(tech_name)
                    break

def detect_patterns(content: str, patterns: Dict[str, int]) -> None:
    """Detect code patterns in file content"""
    for pattern_name, regexes in PATTERN_SIGNATURES.items():
        for regex in regexes:
            matches = re.findall(regex, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                patterns[pattern_name] += len(matches)

def detect_gotchas(file_path: Path, content: str) -> List[Dict[str, Any]]:
    """Detect potential gotchas in code"""
    gotchas = []
    lines = content.splitlines()

    # Look for common anti-patterns
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # TODO/FIXME comments
        if "TODO" in line or "FIXME" in line or "HACK" in line:
            gotchas.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "line": i,
                "type": "todo_fixme",
                "severity": "info",
                "description": line_stripped[:100]
            })

        # Empty exception handlers
        if line_stripped.startswith("except") and "pass" in lines[i] if i < len(lines) else False:
            gotchas.append({
                "file": str(file_path.relative_to(PROJECT_ROOT)),
                "line": i,
                "type": "empty_exception_handler",
                "severity": "warning",
                "description": "Empty exception handler (silent failure)"
            })

        # Hardcoded credentials patterns
        cred_patterns = ["password=", "api_key=", "secret=", "token="]
        for pattern in cred_patterns:
            if pattern in line_stripped.lower() and not line_stripped.startswith("#"):
                # Check if it's actually hardcoded (not env var or config)
                if "os.environ" not in line and "process.env" not in line and "config" not in line.lower():
                    gotchas.append({
                        "file": str(file_path.relative_to(PROJECT_ROOT)),
                        "line": i,
                        "type": "potential_hardcoded_secret",
                        "severity": "critical",
                        "description": "Possible hardcoded credential"
                    })

    return gotchas

def analyze_architecture(tech_stack: Dict[str, List[str]]) -> List[str]:
    """Analyze tech stack to infer architectural patterns"""
    insights = []

    # Detect architecture type
    if "docker" in tech_stack.get("infrastructure", []):
        insights.append("Containerized application (Docker)")

    if "kubernetes" in tech_stack.get("infrastructure", []):
        insights.append("Kubernetes orchestration (microservices likely)")

    # Detect API style
    api_techs = tech_stack.get("api", [])
    if "graphql" in api_techs:
        insights.append("GraphQL API")
    elif any(x in api_techs for x in ["rest", "fastapi", "express", "flask"]):
        insights.append("RESTful API")

    # Detect database type
    db_techs = tech_stack.get("database", [])
    if db_techs:
        insights.append(f"Database: {', '.join(db_techs[:3])}")

    # Detect frontend framework
    fe_techs = tech_stack.get("frontend", [])
    if fe_techs:
        insights.append(f"Frontend: {', '.join(fe_techs)}")

    # Detect authentication
    auth_techs = tech_stack.get("sso", [])
    if auth_techs:
        insights.append(f"Authentication: {', '.join(auth_techs)}")

    return insights

def convert_scan_to_learnings(scan_results: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Convert scan results into learning database format"""
    learnings = {}

    for topic, techs in scan_results["tech_stack"].items():
        if not techs:
            continue

        patterns = []
        gotchas_by_topic = []

        # Create patterns from detected tech
        for tech in techs:
            patterns.append({
                "id": f"{topic}-discovered-{tech}",
                "name": f"{tech.title()} Usage Pattern",
                "description": f"Project uses {tech} (auto-discovered during codebase scan)",
                "example_files": [],
                "confidence": 0.8,
                "use_count": 0,
                "success_rate": 1.0,
                "discovered_by": "codebase_scan",
                "discovered_at": None  # Will be set during save
            })

        # Filter gotchas relevant to this topic
        for gotcha in scan_results["potential_gotchas"]:
            if is_gotcha_relevant_to_topic(gotcha, topic):
                gotchas_by_topic.append({
                    "category": gotcha["type"],
                    "issue": gotcha["description"],
                    "severity": gotcha["severity"],
                    "files": [f"{gotcha['file']}:{gotcha['line']}"],
                    "discovered_by": "codebase_scan"
                })

        learnings[topic] = {
            "patterns": patterns,
            "gotchas": gotchas_by_topic[:10],  # Limit to top 10
            "insights": [insight for insight in scan_results["architectural_insights"]
                        if topic in insight.lower()]
        }

    return learnings

def is_gotcha_relevant_to_topic(gotcha: Dict[str, Any], topic: str) -> bool:
    """Determine if a gotcha is relevant to a specific topic"""
    relevance_map = {
        "infrastructure": ["docker", "k8s", "deploy", "ci"],
        "sso": ["auth", "token", "jwt", "oauth", "saml"],
        "security": ["secret", "password", "credential", "auth", "permission"],
        "api": ["endpoint", "route", "api", "handler"],
        "database": ["query", "sql", "db", "database"],
        "frontend": ["component", "react", "vue", "ui"],
        "testing": ["test", "spec", "mock"]
    }

    gotcha_text = f"{gotcha.get('file', '')} {gotcha.get('description', '')} {gotcha.get('type', '')}".lower()

    keywords = relevance_map.get(topic, [])
    return any(keyword in gotcha_text for keyword in keywords)

def format_scan_report(scan_results: Dict[str, Any]) -> str:
    """Format scan results as human-readable report"""
    lines = ["# Codebase Scan Report\n"]

    # Statistics
    stats = scan_results["file_statistics"]
    lines.append(f"**Files Scanned**: {stats['files_scanned']}")
    lines.append(f"**Total Lines**: {stats['total_lines']:,}")
    lines.append(f"**Average Lines/File**: {stats['avg_lines_per_file']}\n")

    # Architecture
    if scan_results["architectural_insights"]:
        lines.append("## Architectural Insights\n")
        for insight in scan_results["architectural_insights"]:
            lines.append(f"- {insight}")
        lines.append("")

    # Tech Stack
    lines.append("## Detected Technologies\n")
    for topic, techs in scan_results["tech_stack"].items():
        if techs:
            lines.append(f"**{topic.title()}**: {', '.join(techs)}")
    lines.append("")

    # Patterns
    if scan_results["patterns"]:
        lines.append("## Code Patterns Detected\n")
        sorted_patterns = sorted(scan_results["patterns"].items(), key=lambda x: x[1], reverse=True)
        for pattern_name, count in sorted_patterns[:10]:
            lines.append(f"- {pattern_name.replace('_', ' ').title()}: {count} occurrences")
        lines.append("")

    # Gotchas
    critical_gotchas = [g for g in scan_results["potential_gotchas"] if g.get("severity") == "critical"]
    if critical_gotchas:
        lines.append(f"## ⚠️  Critical Issues Found: {len(critical_gotchas)}\n")
        for gotcha in critical_gotchas[:5]:
            lines.append(f"- {gotcha['file']}:{gotcha['line']} - {gotcha['description'][:80]}")
        lines.append("")

    warning_gotchas = [g for g in scan_results["potential_gotchas"] if g.get("severity") == "warning"]
    if warning_gotchas:
        lines.append(f"## Warnings Found: {len(warning_gotchas)}\n")
        for gotcha in warning_gotchas[:5]:
            lines.append(f"- {gotcha['file']}:{gotcha['line']} - {gotcha['type'].replace('_', ' ').title()}")
        lines.append("")

    return "\n".join(lines)
