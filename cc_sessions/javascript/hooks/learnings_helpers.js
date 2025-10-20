#!/usr/bin/env node

/**
 * Learning System Helpers
 *
 * Provides functions for managing the learning database:
 * - Topic detection and relevance scoring
 * - Pattern loading and retrieval
 * - Learning file I/O operations
 */

// ===== IMPORTS ===== //
const fs = require('fs');
const path = require('path');

const { PROJECT_ROOT } = require('./shared_state.js');

// ===== GLOBALS ===== //
const LEARNINGS_DIR = path.join(PROJECT_ROOT, 'sessions', 'learnings');
const INDEX_FILE = path.join(LEARNINGS_DIR, 'learnings-index.json');

// ===== DATA STRUCTURES ===== //

const DEFAULT_TOPICS = {
    "infrastructure": {
        "description": "DevOps, CI/CD, deployments, Docker, K8s, infrastructure",
        "keywords": ["docker", "kubernetes", "k8s", "deploy", "ci/cd", "cicd", "terraform", "ansible", "jenkins", "github actions"],
        "file_patterns": ["*.dockerfile", "Dockerfile", "docker-compose*", "k8s/*", "kubernetes/*", ".github/workflows/*", "*.tf", "*.tfvars"],
        "related_topics": ["security", "api"],
        "last_updated": null
    },
    "sso": {
        "description": "Single Sign-On, OAuth, SAML, authentication flows",
        "keywords": ["oauth", "saml", "jwt", "token", "auth", "sso", "openid", "oidc", "authentication", "login"],
        "file_patterns": ["**/auth/*", "**/sso/*", "**/login/*", "**/oauth/*", "**/saml/*"],
        "related_topics": ["security", "api"],
        "last_updated": null
    },
    "security": {
        "description": "Security vulnerabilities, input validation, crypto, permissions",
        "keywords": ["security", "vulnerability", "xss", "sql injection", "csrf", "cors", "crypto", "encrypt", "hash", "permission", "rbac", "abac"],
        "file_patterns": ["**/security/*", "**/middleware/auth*", "**/permissions/*"],
        "related_topics": ["sso", "api", "database"],
        "last_updated": null
    },
    "api": {
        "description": "REST APIs, GraphQL, endpoints, HTTP, routing",
        "keywords": ["api", "rest", "graphql", "endpoint", "http", "route", "middleware", "fastapi", "express", "flask"],
        "file_patterns": ["**/api/*", "**/routes/*", "**/endpoints/*", "**/controllers/*", "**/handlers/*"],
        "related_topics": ["security", "database"],
        "last_updated": null
    },
    "database": {
        "description": "Database schemas, queries, ORMs, migrations",
        "keywords": ["database", "sql", "postgres", "mysql", "mongo", "orm", "sqlalchemy", "prisma", "typeorm", "migration", "schema"],
        "file_patterns": ["**/models/*", "**/schemas/*", "**/migrations/*", "**/*_model.py", "**/*Model.ts"],
        "related_topics": ["api", "security"],
        "last_updated": null
    },
    "frontend": {
        "description": "UI components, React, Vue, state management",
        "keywords": ["react", "vue", "angular", "component", "ui", "frontend", "redux", "zustand", "state management", "css", "tailwind"],
        "file_patterns": ["**/components/*", "**/views/*", "**/pages/*", "**/*.jsx", "**/*.tsx", "**/*.vue"],
        "related_topics": ["api"],
        "last_updated": null
    },
    "testing": {
        "description": "Unit tests, integration tests, E2E testing",
        "keywords": ["test", "pytest", "jest", "mocha", "vitest", "unittest", "e2e", "integration", "mock"],
        "file_patterns": ["**/tests/*", "**/*_test.py", "**/*.test.ts", "**/*.spec.ts"],
        "related_topics": [],
        "last_updated": null
    }
};

// ===== FUNCTIONS ===== //

function ensureLearningsStructure() {
    /**
     * Ensure the learnings directory structure exists
     */
    fs.mkdirSync(LEARNINGS_DIR, { recursive: true });

    // Create index if it doesn't exist
    if (!fs.existsSync(INDEX_FILE)) {
        initIndex();
    }

    // Create default topic directories
    const index = loadIndex();
    for (const topic of Object.keys(index.topics || {})) {
        const topicDir = path.join(LEARNINGS_DIR, topic);
        fs.mkdirSync(topicDir, { recursive: true });

        // Create default files if they don't exist
        const metaFile = path.join(topicDir, 'meta.json');
        if (!fs.existsSync(metaFile)) {
            const topicData = index.topics[topic];
            fs.writeFileSync(metaFile, JSON.stringify(topicData, null, 2), 'utf-8');
        }

        const patternsFile = path.join(topicDir, 'patterns.json');
        if (!fs.existsSync(patternsFile)) {
            fs.writeFileSync(patternsFile, JSON.stringify({
                successful_patterns: [],
                anti_patterns: []
            }, null, 2), 'utf-8');
        }

        const gotchasFile = path.join(topicDir, 'gotchas.json');
        if (!fs.existsSync(gotchasFile)) {
            fs.writeFileSync(gotchasFile, JSON.stringify({
                file_specific: {},
                general_gotchas: []
            }, null, 2), 'utf-8');
        }

        const historyFile = path.join(topicDir, 'history.json');
        if (!fs.existsSync(historyFile)) {
            fs.writeFileSync(historyFile, JSON.stringify({
                tasks_completed: [],
                common_errors: {}
            }, null, 2), 'utf-8');
        }
    }
}

function initIndex() {
    /**
     * Initialize the learnings index with default topics
     */
    const indexData = {
        topics: DEFAULT_TOPICS,
        last_updated: new Date().toISOString()
    };
    fs.writeFileSync(INDEX_FILE, JSON.stringify(indexData, null, 2), 'utf-8');
}

function loadIndex() {
    /**
     * Load the learnings index
     *
     * @returns {Object} Index data
     */
    if (!fs.existsSync(INDEX_FILE)) {
        initIndex();
    }
    return JSON.parse(fs.readFileSync(INDEX_FILE, 'utf-8'));
}

function saveIndex(index) {
    /**
     * Save the learnings index
     *
     * @param {Object} index - Index data to save
     */
    index.last_updated = new Date().toISOString();
    fs.writeFileSync(INDEX_FILE, JSON.stringify(index, null, 2), 'utf-8');
}

function addTopic(topicName, description, keywords, filePatterns, relatedTopics = null) {
    /**
     * Add a new topic to the index
     *
     * @param {string} topicName - Name of the topic
     * @param {string} description - Description of the topic
     * @param {Array<string>} keywords - Keywords for the topic
     * @param {Array<string>} filePatterns - File patterns for the topic
     * @param {Array<string>} relatedTopics - Related topics
     * @returns {boolean} Success status
     */
    const index = loadIndex();

    if (index.topics[topicName]) {
        return false;
    }

    index.topics[topicName] = {
        description: description,
        keywords: keywords,
        file_patterns: filePatterns,
        related_topics: relatedTopics || [],
        last_updated: new Date().toISOString()
    };

    saveIndex(index);

    // Create topic directory structure
    const topicDir = path.join(LEARNINGS_DIR, topicName);
    fs.mkdirSync(topicDir, { recursive: true });

    // Create empty data files
    fs.writeFileSync(
        path.join(topicDir, 'meta.json'),
        JSON.stringify(index.topics[topicName], null, 2),
        'utf-8'
    );
    fs.writeFileSync(
        path.join(topicDir, 'patterns.json'),
        JSON.stringify({ successful_patterns: [], anti_patterns: [] }, null, 2),
        'utf-8'
    );
    fs.writeFileSync(
        path.join(topicDir, 'gotchas.json'),
        JSON.stringify({ file_specific: {}, general_gotchas: [] }, null, 2),
        'utf-8'
    );
    fs.writeFileSync(
        path.join(topicDir, 'history.json'),
        JSON.stringify({ tasks_completed: [], common_errors: {} }, null, 2),
        'utf-8'
    );

    return true;
}

function detectRelevantTopics(taskContent, filePaths = null) {
    /**
     * Detect relevant topics based on task description and file paths
     *
     * @param {string} taskContent - Task description content
     * @param {Array<string>} filePaths - File paths to analyze
     * @returns {Array<string>} List of topic names sorted by relevance score
     */
    const index = loadIndex();
    const topicScores = {};

    // Convert content to lowercase for case-insensitive matching
    const contentLower = taskContent.toLowerCase();

    for (const [topicName, topicData] of Object.entries(index.topics)) {
        let score = 0;

        // Check keywords in content
        for (const keyword of topicData.keywords) {
            if (contentLower.includes(keyword.toLowerCase())) {
                score += 2;
            }
        }

        // Check file patterns if files provided
        if (filePaths) {
            for (const filePath of filePaths) {
                const pathStr = filePath.toLowerCase();
                for (const pattern of topicData.file_patterns) {
                    // Simple pattern matching (could be enhanced with minimatch)
                    const patternParts = pattern.toLowerCase().replace(/\*\*/g, '').replace(/\*/g, '').split('/');
                    if (patternParts.some(part => part && pathStr.includes(part))) {
                        score += 3;
                    }
                }
            }
        }

        if (score > 0) {
            topicScores[topicName] = score;
        }
    }

    // Sort by score descending
    const sortedTopics = Object.entries(topicScores)
        .sort((a, b) => b[1] - a[1])
        .map(([topic, score]) => topic);

    return sortedTopics;
}

function loadTopicPatterns(topic) {
    /**
     * Load patterns for a specific topic
     *
     * @param {string} topic - Topic name
     * @returns {Object} Patterns data
     */
    const patternsFile = path.join(LEARNINGS_DIR, topic, 'patterns.json');
    if (!fs.existsSync(patternsFile)) {
        return { successful_patterns: [], anti_patterns: [] };
    }
    return JSON.parse(fs.readFileSync(patternsFile, 'utf-8'));
}

function loadTopicGotchas(topic) {
    /**
     * Load gotchas for a specific topic
     *
     * @param {string} topic - Topic name
     * @returns {Object} Gotchas data
     */
    const gotchasFile = path.join(LEARNINGS_DIR, topic, 'gotchas.json');
    if (!fs.existsSync(gotchasFile)) {
        return { file_specific: {}, general_gotchas: [] };
    }
    return JSON.parse(fs.readFileSync(gotchasFile, 'utf-8'));
}

function loadTopicHistory(topic) {
    /**
     * Load history for a specific topic
     *
     * @param {string} topic - Topic name
     * @returns {Object} History data
     */
    const historyFile = path.join(LEARNINGS_DIR, topic, 'history.json');
    if (!fs.existsSync(historyFile)) {
        return { tasks_completed: [], common_errors: {} };
    }
    return JSON.parse(fs.readFileSync(historyFile, 'utf-8'));
}

function formatLearningsForProtocol(topics) {
    /**
     * Format learnings into a readable protocol section
     *
     * @param {Array<string>} topics - Topic names to format
     * @returns {string} Formatted protocol section
     */
    if (!topics || topics.length === 0) {
        return "";
    }

    const output = ["## 📚 Learning Context\n"];
    output.push(`**Loaded Topics**: ${topics.join(', ')}\n`);

    for (const topic of topics) {
        const patterns = loadTopicPatterns(topic);
        const gotchas = loadTopicGotchas(topic);

        // Show top 3 successful patterns
        const successful = (patterns.successful_patterns || []).slice(0, 3);
        if (successful.length > 0) {
            output.push(`\n### ${topic.charAt(0).toUpperCase() + topic.slice(1)} - Recommended Patterns:\n`);
            for (const pattern of successful) {
                output.push(`- **${pattern.name}**: ${pattern.description}`);
                if (pattern.example_files) {
                    output.push(` (see ${pattern.example_files.join(', ')})`);
                }
                output.push("\n");
            }
        }

        // Show important gotchas
        const fileGotchas = gotchas.file_specific || {};
        const generalGotchas = gotchas.general_gotchas || [];

        if (Object.keys(fileGotchas).length > 0 || generalGotchas.length > 0) {
            output.push(`\n### ${topic.charAt(0).toUpperCase() + topic.slice(1)} - Known Gotchas:\n`);

            // File-specific gotchas
            for (const [filePath, issues] of Object.entries(fileGotchas).slice(0, 3)) {
                for (const issue of issues.slice(0, 2)) {  // Max 2 per file
                    output.push(`⚠️ \`${filePath}:${issue.line_range || '??'}\` - ${issue.issue}\n`);
                }
            }

            // General gotchas
            for (const gotcha of generalGotchas.slice(0, 3)) {
                output.push(`⚠️ ${gotcha.issue}`);
                if (gotcha.solution) {
                    output.push(` → ${gotcha.solution}`);
                }
                output.push("\n");
            }
        }

        // Show anti-patterns to avoid
        const anti = (patterns.anti_patterns || []).slice(0, 2);
        if (anti.length > 0) {
            output.push(`\n### ${topic.charAt(0).toUpperCase() + topic.slice(1)} - Anti-Patterns to Avoid:\n`);
            for (const pattern of anti) {
                output.push(`- **${pattern.name}**: ${pattern.problem}`);
                if (pattern.solution) {
                    output.push(` → ${pattern.solution}`);
                }
                output.push("\n");
            }
        }
    }

    return output.join("");
}

function listAllTopics() {
    /**
     * List all available learning topics
     *
     * @returns {Array<string>} Sorted list of topic names
     */
    const index = loadIndex();
    return Object.keys(index.topics).sort();
}

function getTopicInfo(topic) {
    /**
     * Get information about a specific topic
     *
     * @param {string} topic - Topic name
     * @returns {Object|null} Topic information or null if not found
     */
    const index = loadIndex();
    return index.topics[topic] || null;
}

// ===== EXPORTS ===== //
module.exports = {
    ensureLearningsStructure,
    initIndex,
    loadIndex,
    saveIndex,
    addTopic,
    detectRelevantTopics,
    loadTopicPatterns,
    loadTopicGotchas,
    loadTopicHistory,
    formatLearningsForProtocol,
    listAllTopics,
    getTopicInfo,
    LEARNINGS_DIR,
    INDEX_FILE,
    DEFAULT_TOPICS
};
