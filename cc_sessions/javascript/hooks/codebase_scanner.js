#!/usr/bin/env node

/**
 * Codebase Scanner
 *
 * Analyzes existing codebase to discover patterns, tech stack, and potential gotchas.
 * Pre-populates the learning database with discovered information.
 */

// ===== IMPORTS ===== //
const fs = require('fs');
const path = require('path');

const { PROJECT_ROOT } = require('./shared_state.js');

// ===== GLOBALS ===== //

// File patterns for tech detection
const TECH_SIGNATURES = {
    "infrastructure": {
        "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
        "kubernetes": ["k8s/", "kubernetes/", "*.yaml", "*.yml"],
        "terraform": ["*.tf", "*.tfvars", "terraform/"],
        "ansible": ["ansible/", "playbook.yml", "*.ansible.yml"],
        "ci_cd": [".github/workflows/", ".gitlab-ci.yml", "Jenkinsfile", ".circleci/"]
    },
    "sso": {
        "oauth": ["oauth", "OAuth", "auth/oauth", "oauth2"],
        "saml": ["saml", "SAML", "auth/saml"],
        "jwt": ["jwt", "JWT", "jsonwebtoken"],
        "oidc": ["oidc", "openid", "OpenID"]
    },
    "security": {
        "crypto": ["crypto", "encryption", "bcrypt", "argon2", "pbkdf2"],
        "auth": ["auth", "authentication", "authorize", "permission", "rbac"],
        "validation": ["validator", "sanitize", "validate"]
    },
    "api": {
        "rest": ["api/", "routes/", "endpoints/", "controllers/", "handlers/"],
        "graphql": ["graphql", "schema.graphql", "resolvers"],
        "fastapi": ["fastapi", "FastAPI"],
        "express": ["express", "app.use"],
        "flask": ["flask", "Flask", "@app.route"]
    },
    "database": {
        "postgres": ["psycopg2", "postgresql", "postgres"],
        "mysql": ["mysql", "pymysql", "MySQL"],
        "mongodb": ["mongo", "mongodb", "pymongo"],
        "sqlalchemy": ["sqlalchemy", "SQLAlchemy", "Base.metadata"],
        "prisma": ["prisma", "@prisma/client", "schema.prisma"],
        "typeorm": ["typeorm", "TypeORM", "@Entity"]
    },
    "frontend": {
        "react": ["react", "React", "useState", "useEffect", ".jsx", ".tsx"],
        "vue": ["vue", "Vue", ".vue", "createApp"],
        "angular": ["angular", "@angular/", "ng-"],
        "svelte": ["svelte", "Svelte"]
    },
    "testing": {
        "pytest": ["pytest", "test_*.py", "conftest.py"],
        "jest": ["jest", "*.test.js", "*.test.ts", "*.spec.js"],
        "mocha": ["mocha", "describe(", "it("],
        "vitest": ["vitest", "*.test.ts"]
    }
};

// Common patterns to detect
const PATTERN_SIGNATURES = {
    "error_handling": [
        /try\s*{/,
        /try:/,
        /catch\s*\(/,
        /except\s+\w+/,
        /\.catch\(/,
        /throw new/,
        /raise\s+\w+/
    ],
    "async_patterns": [
        /async\s+def\s+\w+/,
        /async\s+function\s+\w+/,
        /await\s+/,
        /asyncio\./,
        /Promise\./,
        /\.then\(/
    ],
    "validation": [
        /validate\w*\(/,
        /sanitize\w*\(/,
        /if\s+not\s+\w+:/,
        /if\s*\(\s*!\w+/,
        /assert\s+/,
        /\.required\(\)/
    ],
    "authentication": [
        /@login_required/,
        /@requires_auth/,
        /authenticate\(/,
        /verify_token/,
        /check_permission/,
        /is_authenticated/
    ],
    "database_queries": [
        /\.query\(/,
        /\.filter\(/,
        /SELECT\s+/,
        /INSERT\s+INTO/,
        /UPDATE\s+/,
        /DELETE\s+FROM/,
        /\.find\(/,
        /\.findOne\(/
    ],
    "configuration": [
        /os\.environ\./,
        /process\.env\./,
        /config\./,
        /settings\./,
        /\.env/,
        /CONFIG\[/
    ]
};

// ===== FUNCTIONS ===== //

function scanCodebase(maxFiles = 500) {
    /**
     * Scan the codebase and return discovered patterns and tech stack
     *
     * @param {number} maxFiles - Maximum number of files to scan (prevent huge scans)
     * @returns {Object} Dictionary with discovered information
     */
    const results = {
        tech_stack: {},
        patterns: {},
        file_statistics: {},
        potential_gotchas: [],
        architectural_insights: []
    };

    // Determine which directories to scan
    const scanDirs = getScanDirectories();

    let filesScanned = 0;
    let totalLines = 0;

    for (const scanDir of scanDirs) {
        if (filesScanned >= maxFiles) {
            break;
        }

        const files = walkDirectory(scanDir);
        for (const filePath of files) {
            if (filesScanned >= maxFiles) {
                break;
            }

            // Skip certain files/directories
            if (shouldSkipFile(filePath)) {
                continue;
            }

            filesScanned++;

            // Detect tech stack from file
            detectTechFromFile(filePath, results.tech_stack);

            // Analyze file content if it's a code file
            if (isCodeFile(filePath)) {
                try {
                    const content = fs.readFileSync(filePath, { encoding: 'utf-8' });
                    const lines = content.split('\n');
                    totalLines += lines.length;

                    // Detect patterns
                    detectPatterns(content, results.patterns);

                    // Look for potential gotchas
                    const gotchas = detectGotchas(filePath, content);
                    results.potential_gotchas.push(...gotchas);
                } catch (err) {
                    // Skip files that can't be read
                }
            }
        }
    }

    results.file_statistics = {
        files_scanned: filesScanned,
        total_lines: totalLines,
        avg_lines_per_file: filesScanned > 0 ? Math.floor(totalLines / filesScanned) : 0
    };

    // Analyze architecture
    results.architectural_insights = analyzeArchitecture(results.tech_stack);

    return results;
}

function getScanDirectories() {
    /**
     * Get list of directories to scan, excluding common non-code dirs
     *
     * @returns {Array<string>} List of directory paths
     */
    const excludeDirs = new Set([
        "node_modules", "venv", ".venv", "env", ".env", "dist", "build",
        "__pycache__", ".git", ".pytest_cache", "coverage", ".next",
        "target", "out", ".cache", "vendor", ".tox"
    ]);

    const scanDirs = [];
    const items = fs.readdirSync(PROJECT_ROOT);
    for (const item of items) {
        const itemPath = path.join(PROJECT_ROOT, item);
        const stats = fs.statSync(itemPath);
        if (stats.isDirectory() && !excludeDirs.has(item) && !item.startsWith('.')) {
            scanDirs.push(itemPath);
        }
    }

    return scanDirs;
}

function walkDirectory(dir) {
    /**
     * Recursively walk directory and return all file paths
     *
     * @param {string} dir - Directory to walk
     * @returns {Array<string>} List of file paths
     */
    let files = [];
    try {
        const items = fs.readdirSync(dir);
        for (const item of items) {
            const itemPath = path.join(dir, item);
            try {
                const stats = fs.statSync(itemPath);
                if (stats.isDirectory()) {
                    files = files.concat(walkDirectory(itemPath));
                } else {
                    files.push(itemPath);
                }
            } catch (err) {
                // Skip files/dirs we can't access
            }
        }
    } catch (err) {
        // Skip directories we can't read
    }
    return files;
}

function shouldSkipFile(filePath) {
    /**
     * Check if file should be skipped during scan
     *
     * @param {string} filePath - Path to file
     * @returns {boolean} True if should skip
     */
    const skipPatterns = [
        ".min.js", ".min.css", ".map", ".lock", ".log",
        "package-lock.json", "yarn.lock", "poetry.lock",
        ".pyc", ".pyo", ".so", ".dylib", ".dll"
    ];

    // Skip by suffix
    for (const pattern of skipPatterns) {
        if (filePath.endsWith(pattern)) {
            return true;
        }
    }

    // Skip hidden files
    const fileName = path.basename(filePath);
    if (fileName.startsWith('.')) {
        return true;
    }

    // Skip large files (> 1MB)
    try {
        const stats = fs.statSync(filePath);
        if (stats.size > 1000000) {
            return true;
        }
    } catch (err) {
        return true;
    }

    return false;
}

function isCodeFile(filePath) {
    /**
     * Check if file is a code file worth analyzing
     *
     * @param {string} filePath - Path to file
     * @returns {boolean} True if code file
     */
    const codeExtensions = new Set([
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
        '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
        '.kt', '.scala', '.sh', '.bash', '.zsh', '.yaml', '.yml',
        '.json', '.toml', '.ini', '.conf', '.sql'
    ]);
    return codeExtensions.has(path.extname(filePath));
}

function detectTechFromFile(filePath, techStack) {
    /**
     * Detect technology from file path and name
     *
     * @param {string} filePath - Path to file
     * @param {Object} techStack - Tech stack dictionary to update
     */
    const fileStr = filePath.toLowerCase();
    const fileName = path.basename(filePath).toLowerCase();

    for (const [topic, techPatterns] of Object.entries(TECH_SIGNATURES)) {
        for (const [techName, patterns] of Object.entries(techPatterns)) {
            for (const pattern of patterns) {
                if (fileStr.includes(pattern.toLowerCase()) || fileName === pattern.toLowerCase()) {
                    if (!techStack[topic]) {
                        techStack[topic] = [];
                    }
                    if (!techStack[topic].includes(techName)) {
                        techStack[topic].push(techName);
                    }
                    break;
                }
            }
        }
    }
}

function detectPatterns(content, patterns) {
    /**
     * Detect code patterns in file content
     *
     * @param {string} content - File content
     * @param {Object} patterns - Patterns dictionary to update
     */
    for (const [patternName, regexes] of Object.entries(PATTERN_SIGNATURES)) {
        for (const regex of regexes) {
            const matches = content.match(new RegExp(regex, 'gim'));
            if (matches) {
                patterns[patternName] = (patterns[patternName] || 0) + matches.length;
            }
        }
    }
}

function detectGotchas(filePath, content) {
    /**
     * Detect potential gotchas in code
     *
     * @param {string} filePath - Path to file
     * @param {string} content - File content
     * @returns {Array<Object>} List of gotchas
     */
    const gotchas = [];
    const lines = content.split('\n');

    // Look for common anti-patterns
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const lineStripped = line.trim();

        // TODO/FIXME comments
        if (lineStripped.includes("TODO") || lineStripped.includes("FIXME") || lineStripped.includes("HACK")) {
            gotchas.push({
                file: path.relative(PROJECT_ROOT, filePath),
                line: i + 1,
                type: "todo_fixme",
                severity: "info",
                description: lineStripped.substring(0, 100)
            });
        }

        // Empty exception handlers
        if (lineStripped.startsWith("except") && i + 1 < lines.length && lines[i + 1].trim() === "pass") {
            gotchas.push({
                file: path.relative(PROJECT_ROOT, filePath),
                line: i + 1,
                type: "empty_exception_handler",
                severity: "warning",
                description: "Empty exception handler (silent failure)"
            });
        }

        // Hardcoded credentials patterns
        const credPatterns = ["password=", "api_key=", "secret=", "token="];
        for (const pattern of credPatterns) {
            if (lineStripped.toLowerCase().includes(pattern) && !lineStripped.startsWith("#")) {
                // Check if it's actually hardcoded (not env var or config)
                if (!line.includes("os.environ") && !line.includes("process.env") && !line.toLowerCase().includes("config")) {
                    gotchas.push({
                        file: path.relative(PROJECT_ROOT, filePath),
                        line: i + 1,
                        type: "potential_hardcoded_secret",
                        severity: "critical",
                        description: "Possible hardcoded credential"
                    });
                }
            }
        }
    }

    return gotchas;
}

function analyzeArchitecture(techStack) {
    /**
     * Analyze tech stack to infer architectural patterns
     *
     * @param {Object} techStack - Discovered tech stack
     * @returns {Array<string>} List of insights
     */
    const insights = [];

    // Detect architecture type
    if ((techStack.infrastructure || []).includes("docker")) {
        insights.push("Containerized application (Docker)");
    }

    if ((techStack.infrastructure || []).includes("kubernetes")) {
        insights.push("Kubernetes orchestration (microservices likely)");
    }

    // Detect API style
    const apiTechs = techStack.api || [];
    if (apiTechs.includes("graphql")) {
        insights.push("GraphQL API");
    } else if (apiTechs.some(x => ["rest", "fastapi", "express", "flask"].includes(x))) {
        insights.push("RESTful API");
    }

    // Detect database type
    const dbTechs = techStack.database || [];
    if (dbTechs.length > 0) {
        insights.push(`Database: ${dbTechs.slice(0, 3).join(', ')}`);
    }

    // Detect frontend framework
    const feTechs = techStack.frontend || [];
    if (feTechs.length > 0) {
        insights.push(`Frontend: ${feTechs.join(', ')}`);
    }

    // Detect authentication
    const authTechs = techStack.sso || [];
    if (authTechs.length > 0) {
        insights.push(`Authentication: ${authTechs.join(', ')}`);
    }

    return insights;
}

function convertScanToLearnings(scanResults) {
    /**
     * Convert scan results into learning database format
     *
     * @param {Object} scanResults - Scan results
     * @returns {Object} Learnings data
     */
    const learnings = {};

    for (const [topic, techs] of Object.entries(scanResults.tech_stack)) {
        if (!techs || techs.length === 0) {
            continue;
        }

        const patterns = [];
        const gotchasByTopic = [];

        // Create patterns from detected tech
        for (const tech of techs) {
            patterns.push({
                id: `${topic}-discovered-${tech}`,
                name: `${tech.charAt(0).toUpperCase() + tech.slice(1)} Usage Pattern`,
                description: `Project uses ${tech} (auto-discovered during codebase scan)`,
                example_files: [],
                confidence: 0.8,
                use_count: 0,
                success_rate: 1.0,
                discovered_by: "codebase_scan",
                discovered_at: null  // Will be set during save
            });
        }

        // Filter gotchas relevant to this topic
        for (const gotcha of scanResults.potential_gotchas) {
            if (isGotchaRelevantToTopic(gotcha, topic)) {
                gotchasByTopic.push({
                    category: gotcha.type,
                    issue: gotcha.description,
                    severity: gotcha.severity,
                    files: [`${gotcha.file}:${gotcha.line}`],
                    discovered_by: "codebase_scan"
                });
            }
        }

        learnings[topic] = {
            patterns: patterns,
            gotchas: gotchasByTopic.slice(0, 10),  // Limit to top 10
            insights: scanResults.architectural_insights.filter(insight =>
                insight.toLowerCase().includes(topic)
            )
        };
    }

    return learnings;
}

function isGotchaRelevantToTopic(gotcha, topic) {
    /**
     * Determine if a gotcha is relevant to a specific topic
     *
     * @param {Object} gotcha - Gotcha object
     * @param {string} topic - Topic name
     * @returns {boolean} True if relevant
     */
    const relevanceMap = {
        "infrastructure": ["docker", "k8s", "deploy", "ci"],
        "sso": ["auth", "token", "jwt", "oauth", "saml"],
        "security": ["secret", "password", "credential", "auth", "permission"],
        "api": ["endpoint", "route", "api", "handler"],
        "database": ["query", "sql", "db", "database"],
        "frontend": ["component", "react", "vue", "ui"],
        "testing": ["test", "spec", "mock"]
    };

    const gotchaText = `${gotcha.file || ''} ${gotcha.description || ''} ${gotcha.type || ''}`.toLowerCase();

    const keywords = relevanceMap[topic] || [];
    return keywords.some(keyword => gotchaText.includes(keyword));
}

function formatScanReport(scanResults) {
    /**
     * Format scan results as human-readable report
     *
     * @param {Object} scanResults - Scan results
     * @returns {string} Formatted report
     */
    const lines = ["# Codebase Scan Report\n"];

    // Statistics
    const stats = scanResults.file_statistics;
    lines.push(`**Files Scanned**: ${stats.files_scanned}`);
    lines.push(`**Total Lines**: ${stats.total_lines.toLocaleString()}`);
    lines.push(`**Average Lines/File**: ${stats.avg_lines_per_file}\n`);

    // Architecture
    if (scanResults.architectural_insights.length > 0) {
        lines.push("## Architectural Insights\n");
        for (const insight of scanResults.architectural_insights) {
            lines.push(`- ${insight}`);
        }
        lines.push("");
    }

    // Tech Stack
    lines.push("## Detected Technologies\n");
    for (const [topic, techs] of Object.entries(scanResults.tech_stack)) {
        if (techs && techs.length > 0) {
            lines.push(`**${topic.charAt(0).toUpperCase() + topic.slice(1)}**: ${techs.join(', ')}`);
        }
    }
    lines.push("");

    // Patterns
    if (Object.keys(scanResults.patterns).length > 0) {
        lines.push("## Code Patterns Detected\n");
        const sortedPatterns = Object.entries(scanResults.patterns)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        for (const [patternName, count] of sortedPatterns) {
            lines.push(`- ${patternName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}: ${count} occurrences`);
        }
        lines.push("");
    }

    // Gotchas
    const criticalGotchas = scanResults.potential_gotchas.filter(g => g.severity === "critical");
    if (criticalGotchas.length > 0) {
        lines.push(`## ⚠️  Critical Issues Found: ${criticalGotchas.length}\n`);
        for (const gotcha of criticalGotchas.slice(0, 5)) {
            lines.push(`- ${gotcha.file}:${gotcha.line} - ${gotcha.description.substring(0, 80)}`);
        }
        lines.push("");
    }

    const warningGotchas = scanResults.potential_gotchas.filter(g => g.severity === "warning");
    if (warningGotchas.length > 0) {
        lines.push(`## Warnings Found: ${warningGotchas.length}\n`);
        for (const gotcha of warningGotchas.slice(0, 5)) {
            lines.push(`- ${gotcha.file}:${gotcha.line} - ${gotcha.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}`);
        }
        lines.push("");
    }

    return lines.join('\n');
}

// ===== EXPORTS ===== //
module.exports = {
    scanCodebase,
    convertScanToLearnings,
    formatScanReport,
    TECH_SIGNATURES,
    PATTERN_SIGNATURES
};
