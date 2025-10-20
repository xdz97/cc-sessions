#!/usr/bin/env node
/**
 * Learning Commands
 *
 * API commands for managing the learning system:
 * - List topics
 * - Show topic details
 * - Add new topics
 * - Initialize learning system
 * - Show relevant topics for current context
 */

const fs = require('fs');
const path = require('path');

// Import from hooks
const { loadState, editState, PROJECT_ROOT } = require('../hooks/shared_state.js');
const {
    ensureLearningsStructure,
    listAllTopics,
    getTopicInfo,
    addTopic,
    detectRelevantTopics,
    formatLearningsForProtocol,
    loadIndex,
    saveIndex,
    LEARNINGS_DIR
} = require('../hooks/learnings_helpers.js');
const {
    scanCodebase,
    convertScanToLearnings,
    formatScanReport
} = require('../hooks/codebase_scanner.js');

// ===== COMMANDS ===== //

function cmdListTopics(args, jsonOutput = false) {
    /**
     * List all available learning topics
     */
    ensureLearningsStructure();
    const topics = listAllTopics();

    if (jsonOutput) {
        const output = { topics: [] };
        for (const topic of topics) {
            try {
                const info = getTopicInfo(topic);
                output.topics.push({
                    name: topic,
                    description: info.description,
                    pattern_count: info.pattern_count,
                    gotcha_count: info.gotcha_count,
                    usage_count: info.usage_count
                });
            } catch (error) {
                // Skip topics that can't be loaded
            }
        }
        console.log(JSON.stringify(output, null, 2));
        return;
    }

    console.log('\n📚 Available Learning Topics:\n');
    for (const topic of topics) {
        try {
            const info = getTopicInfo(topic);
            console.log(`  ${topic}`);
            console.log(`    ${info.description}`);
            console.log(`    Patterns: ${info.pattern_count}, Gotchas: ${info.gotcha_count}, Used: ${info.usage_count} times`);
            console.log('');
        } catch (error) {
            console.log(`  ${topic} (error loading details)`);
        }
    }
}

function cmdShowTopic(args, jsonOutput = false) {
    /**
     * Show detailed information about a specific topic
     */
    if (args.length === 0) {
        console.error('Error: Topic name required. Use: sessions learnings show <topic>');
        process.exit(1);
    }

    const topicName = args[0];
    ensureLearningsStructure();

    try {
        const info = getTopicInfo(topicName);

        if (jsonOutput) {
            console.log(JSON.stringify(info, null, 2));
            return;
        }

        console.log(`\n📚 Topic: ${info.name}\n`);
        console.log(`Description: ${info.description}`);
        console.log(`\nKeywords: ${info.keywords.join(', ')}`);
        console.log(`File Patterns: ${info.file_patterns.join(', ')}`);
        if (info.related_topics && info.related_topics.length > 0) {
            console.log(`Related Topics: ${info.related_topics.join(', ')}`);
        }
        console.log(`\nStatistics:`);
        console.log(`  Patterns: ${info.pattern_count}`);
        console.log(`  Gotchas: ${info.gotcha_count}`);
        console.log(`  Times Used: ${info.usage_count}`);
        console.log(`  Last Updated: ${info.last_updated || 'Never'}\n`);

    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
}

function cmdAddTopic(args, jsonOutput = false) {
    /**
     * Add a new learning topic
     */
    if (args.length < 2) {
        console.error('Error: Usage: sessions learnings add <topic> <description> [keywords...]');
        process.exit(1);
    }

    const topicName = args[0];
    const description = args[1];
    const keywords = args.slice(2);

    ensureLearningsStructure();

    try {
        addTopic(topicName, description, keywords, [], []);

        if (jsonOutput) {
            console.log(JSON.stringify({ success: true, topic: topicName }, null, 2));
            return;
        }

        console.log(`\n✓ Added new topic: ${topicName}`);
        console.log(`  Description: ${description}`);
        console.log(`  Keywords: ${keywords.join(', ')}\n`);

    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
}

function cmdRelevantTopics(args, jsonOutput = false) {
    /**
     * Show topics relevant to current task or provided text
     */
    ensureLearningsStructure();

    // Get task content if available
    const state = loadState();
    let taskContent = '';

    if (state && state.current_task && state.current_task.file) {
        const taskFile = path.join(PROJECT_ROOT, 'sessions', 'tasks', state.current_task.file);
        if (fs.existsSync(taskFile)) {
            taskContent = fs.readFileSync(taskFile, 'utf-8');
        }
    }

    // Or use provided text
    if (args.length > 0) {
        taskContent = args.join(' ');
    }

    if (!taskContent) {
        console.error('Error: No task active and no text provided');
        process.exit(1);
    }

    const relevantTopics = detectRelevantTopics(taskContent);

    if (jsonOutput) {
        console.log(JSON.stringify({ relevant_topics: relevantTopics }, null, 2));
        return;
    }

    if (relevantTopics.length === 0) {
        console.log('\nNo relevant topics detected for this content.\n');
        return;
    }

    console.log('\n📚 Relevant Topics:\n');
    for (const topic of relevantTopics) {
        try {
            const info = getTopicInfo(topic);
            console.log(`  ${topic}: ${info.description}`);
        } catch (error) {
            console.log(`  ${topic}`);
        }
    }
    console.log('');
}

function cmdInitLearnings(args, jsonOutput = false) {
    /**
     * Initialize the learning system
     */
    const shouldScan = args.includes('--scan');

    ensureLearningsStructure();

    if (!shouldScan) {
        if (jsonOutput) {
            console.log(JSON.stringify({ success: true, scanned: false }, null, 2));
            return;
        }

        console.log('\n✓ Learning system initialized with default topics');
        console.log('  Use --scan flag to scan codebase and pre-populate learnings\n');
        return;
    }

    // Perform codebase scan
    console.log('\n🔍 Scanning codebase...');
    const scanResults = scanCodebase(500);

    console.log(`\n  Files scanned: ${scanResults.file_statistics.files_scanned}`);
    console.log(`  Total lines: ${scanResults.file_statistics.total_lines.toLocaleString()}\n`);

    // Convert scan results to learnings
    const learningsData = convertScanToLearnings(scanResults);

    // Save to learning files
    for (const [topic, data] of Object.entries(learningsData)) {
        const topicDir = path.join(LEARNINGS_DIR, 'topics', topic);

        if (!fs.existsSync(topicDir)) {
            continue; // Skip topics that don't have directories
        }

        // Save patterns
        if (data.patterns && data.patterns.length > 0) {
            const patternsFile = path.join(topicDir, 'patterns.json');
            fs.writeFileSync(patternsFile, JSON.stringify({ patterns: data.patterns }, null, 2), 'utf-8');
        }

        // Save gotchas
        if (data.gotchas && data.gotchas.length > 0) {
            const gotchasFile = path.join(topicDir, 'gotchas.json');
            fs.writeFileSync(gotchasFile, JSON.stringify({ gotchas: data.gotchas }, null, 2), 'utf-8');
        }
    }

    if (jsonOutput) {
        console.log(JSON.stringify({
            success: true,
            scanned: true,
            files_scanned: scanResults.file_statistics.files_scanned,
            learnings_populated: Object.keys(learningsData).length
        }, null, 2));
        return;
    }

    console.log('✓ Learning system initialized and populated with codebase scan\n');
    console.log(formatScanReport(scanResults));
}

function cmdEnableLearnings(args, jsonOutput = false) {
    /**
     * Enable automatic learning loading
     */
    editState(s => {
        s.learnings.enabled = true;
        s.learnings.auto_load = true;
    });

    if (jsonOutput) {
        console.log(JSON.stringify({ enabled: true }, null, 2));
        return;
    }

    console.log('\n✓ Learning system enabled');
    console.log('  Learnings will auto-load at task startup\n');
}

function cmdDisableLearnings(args, jsonOutput = false) {
    /**
     * Disable automatic learning loading
     */
    editState(s => {
        s.learnings.enabled = false;
        s.learnings.auto_load = false;
    });

    if (jsonOutput) {
        console.log(JSON.stringify({ enabled: false }, null, 2));
        return;
    }

    console.log('\n✓ Learning system disabled');
    console.log('  Learnings will not auto-load at task startup\n');
}

function cmdStatus(args, jsonOutput = false) {
    /**
     * Show learning system status
     */
    const state = loadState();
    const learningsEnabled = state.learnings ? state.learnings.enabled : false;
    const autoLoad = state.learnings ? state.learnings.auto_load : false;
    const activeTopics = state.learnings ? state.learnings.active_topics : [];

    ensureLearningsStructure();
    const allTopics = listAllTopics();

    if (jsonOutput) {
        console.log(JSON.stringify({
            enabled: learningsEnabled,
            auto_load: autoLoad,
            active_topics: activeTopics,
            total_topics: allTopics.length
        }, null, 2));
        return;
    }

    console.log('\n📚 Learning System Status:\n');
    console.log(`  Enabled: ${learningsEnabled ? 'Yes' : 'No'}`);
    console.log(`  Auto-load: ${autoLoad ? 'Yes' : 'No'}`);
    console.log(`  Total Topics: ${allTopics.length}`);

    if (activeTopics.length > 0) {
        console.log(`  Active Topics: ${activeTopics.join(', ')}`);
    } else {
        console.log(`  Active Topics: None`);
    }
    console.log('');
}

// ===== ROUTER ===== //

function routeLearningCommand(subcmd, args, jsonOutput = false) {
    /**
     * Route learning subcommands to appropriate handlers
     */
    const handlers = {
        'list': cmdListTopics,
        'show': cmdShowTopic,
        'add': cmdAddTopic,
        'relevant': cmdRelevantTopics,
        'init': cmdInitLearnings,
        'enable': cmdEnableLearnings,
        'disable': cmdDisableLearnings,
        'status': cmdStatus
    };

    const handler = handlers[subcmd];
    if (!handler) {
        console.error(`Unknown learning command: ${subcmd}`);
        console.error('Available commands: list, show, add, relevant, init, enable, disable, status');
        process.exit(1);
    }

    handler(args, jsonOutput);
}

// ===== EXPORTS ===== //
module.exports = {
    cmdListTopics,
    cmdShowTopic,
    cmdAddTopic,
    cmdRelevantTopics,
    cmdInitLearnings,
    cmdEnableLearnings,
    cmdDisableLearnings,
    cmdStatus,
    routeLearningCommand
};
