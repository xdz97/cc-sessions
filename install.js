#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m'
};

function color(text, colorCode) {
  return `${colorCode}${text}${colors.reset}`;
}

// Determine package and project root
const SCRIPT_DIR = __dirname;
const PROJECT_ROOT = process.cwd();

async function main() {
  console.log(color('\n╔════════════════════════════════════════════════════════════════╗', colors.cyan));
  console.log(color('║         CC-SESSIONS INSTALLER (JavaScript Edition)            ║', colors.cyan));
  console.log(color('╚════════════════════════════════════════════════════════════════╝\n', colors.cyan));

  // Check if already installed
  const sessionsDir = path.join(PROJECT_ROOT, 'sessions');
  if (fs.existsSync(sessionsDir)) {
    console.log(color('⚠️  cc-sessions appears to be already installed (sessions/ directory exists).', colors.yellow));
    console.log(color('Update/reinstall logic will be available in a future version.', colors.yellow));
    console.log(color('Exiting without changes.\n', colors.yellow));
    process.exit(0);
  }

  console.log(color('Installing cc-sessions to: ' + PROJECT_ROOT, colors.cyan));
  console.log();

  try {
    // Create directory structure
    createDirectoryStructure();

    // Copy shared files
    copySharedFiles();

    // Copy JavaScript-specific files
    copyJavaScriptFiles();

    // Configure .claude/settings.json
    await configureSettings();

    // Add reference to CLAUDE.md
    configureCLAUDEmd();

    // Initialize state and config files
    initializeStateFiles();

    console.log(color('\n✅ cc-sessions installed successfully!\n', colors.green));
    console.log(color('Next steps:', colors.bold));
    console.log('  1. Restart your Claude Code session (or run /clear)');
    console.log('  2. The kickstart onboarding will guide you through setup\n');

  } catch (error) {
    console.error(color('\n❌ Installation failed:', colors.red), error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

function createDirectoryStructure() {
  console.log(color('Creating directory structure...', colors.cyan));

  const dirs = [
    '.claude',
    '.claude/agents',
    '.claude/commands',
    'sessions',
    'sessions/tasks',
    'sessions/tasks/done',
    'sessions/tasks/indexes',
    'sessions/hooks',
    'sessions/api',
    'sessions/protocols',
    'sessions/knowledge'
  ];

  for (const dir of dirs) {
    const fullPath = path.join(PROJECT_ROOT, dir);
    if (!fs.existsSync(fullPath)) {
      fs.mkdirSync(fullPath, { recursive: true });
    }
  }
}

function copySharedFiles() {
  console.log(color('Installing shared files...', colors.cyan));

  // Copy agents
  const agentsSource = path.join(SCRIPT_DIR, 'cc_sessions', 'agents');
  const agentsDest = path.join(PROJECT_ROOT, '.claude', 'agents');
  if (fs.existsSync(agentsSource)) {
    copyDirectory(agentsSource, agentsDest);
  }

  // Copy knowledge base
  const knowledgeSource = path.join(SCRIPT_DIR, 'cc_sessions', 'knowledge');
  const knowledgeDest = path.join(PROJECT_ROOT, 'sessions', 'knowledge');
  if (fs.existsSync(knowledgeSource)) {
    copyDirectory(knowledgeSource, knowledgeDest);
  }
}

function copyJavaScriptFiles() {
  console.log(color('Installing JavaScript-specific files...', colors.cyan));

  const jsRoot = path.join(SCRIPT_DIR, 'cc_sessions', 'javascript');

  // Copy statusline
  copyFile(
    path.join(jsRoot, 'statusline.js'),
    path.join(PROJECT_ROOT, 'sessions', 'statusline.js')
  );

  // Copy API
  copyDirectory(
    path.join(jsRoot, 'api'),
    path.join(PROJECT_ROOT, 'sessions', 'api')
  );

  // Copy hooks
  copyDirectory(
    path.join(jsRoot, 'hooks'),
    path.join(PROJECT_ROOT, 'sessions', 'hooks')
  );

  // Copy protocols
  copyDirectory(
    path.join(jsRoot, 'protocols'),
    path.join(PROJECT_ROOT, 'sessions', 'protocols')
  );

  // Copy commands
  copyDirectory(
    path.join(jsRoot, 'commands'),
    path.join(PROJECT_ROOT, '.claude', 'commands')
  );

  // Copy templates to their respective destinations
  const templatesDir = path.join(jsRoot, 'templates');

  copyFile(
    path.join(templatesDir, 'CLAUDE.sessions.md'),
    path.join(PROJECT_ROOT, 'sessions', 'CLAUDE.sessions.md')
  );

  copyFile(
    path.join(templatesDir, 'TEMPLATE.md'),
    path.join(PROJECT_ROOT, 'sessions', 'tasks', 'TEMPLATE.md')
  );

  copyFile(
    path.join(templatesDir, 'h-kickstart-setup.md'),
    path.join(PROJECT_ROOT, 'sessions', 'tasks', 'h-kickstart-setup.md')
  );

  copyFile(
    path.join(templatesDir, 'INDEX_TEMPLATE.md'),
    path.join(PROJECT_ROOT, 'sessions', 'tasks', 'indexes', 'INDEX_TEMPLATE.md')
  );
}

async function configureSettings() {
  console.log(color('Configuring Claude Code hooks...', colors.cyan));

  const settingsPath = path.join(PROJECT_ROOT, '.claude', 'settings.json');
  let settings = {};

  // Load existing settings if they exist
  if (fs.existsSync(settingsPath)) {
    try {
      settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
    } catch (error) {
      console.log(color('⚠️  Could not parse existing settings.json, will create new one', colors.yellow));
    }
  }

  // Define sessions hooks
  const sessionsHooks = {
    UserPromptSubmit: [
      {
        hooks: [
          {
            type: "command",
            command: process.platform === 'win32'
              ? "node \"%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\user_messages.js\""
              : "node $CLAUDE_PROJECT_DIR/sessions/hooks/user_messages.js"
          }
        ]
      }
    ],
    PreToolUse: [
      {
        matcher: "Write|Edit|MultiEdit|Task|Bash",
        hooks: [
          {
            type: "command",
            command: process.platform === 'win32'
              ? "node \"%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\sessions_enforce.js\""
              : "node $CLAUDE_PROJECT_DIR/sessions/hooks/sessions_enforce.js"
          }
        ]
      },
      {
        matcher: "Task",
        hooks: [
          {
            type: "command",
            command: process.platform === 'win32'
              ? "node \"%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\subagent_hooks.js\""
              : "node $CLAUDE_PROJECT_DIR/sessions/hooks/subagent_hooks.js"
          }
        ]
      }
    ],
    PostToolUse: [
      {
        hooks: [
          {
            type: "command",
            command: process.platform === 'win32'
              ? "node \"%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\post_tool_use.js\""
              : "node $CLAUDE_PROJECT_DIR/sessions/hooks/post_tool_use.js"
          }
        ]
      }
    ],
    SessionStart: [
      {
        matcher: "startup|clear",
        hooks: [
          {
            type: "command",
            command: process.platform === 'win32'
              ? "node \"%CLAUDE_PROJECT_DIR%\\sessions\\hooks\\session_start.js\""
              : "node $CLAUDE_PROJECT_DIR/sessions/hooks/session_start.js"
          }
        ]
      }
    ]
  };

  // Initialize hooks object if it doesn't exist
  if (!settings.hooks) {
    settings.hooks = {};
  }

  // Merge each hook type (sessions hooks take precedence)
  for (const [hookType, hookConfig] of Object.entries(sessionsHooks)) {
    if (!settings.hooks[hookType]) {
      settings.hooks[hookType] = [];
    }

    // Add sessions hooks (prepend so they run first)
    settings.hooks[hookType] = [...hookConfig, ...settings.hooks[hookType]];
  }

  // Write updated settings
  fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2));
}

function configureCLAUDEmd() {
  console.log(color('Configuring CLAUDE.md...', colors.cyan));

  const claudePath = path.join(PROJECT_ROOT, 'CLAUDE.md');
  const reference = '@sessions/CLAUDE.sessions.md';

  if (fs.existsSync(claudePath)) {
    let content = fs.readFileSync(claudePath, 'utf-8');

    // Only add if not already present
    if (!content.includes(reference)) {
      // Add at the beginning after any frontmatter
      const lines = content.split('\n');
      let insertIndex = 0;

      // Skip frontmatter if it exists
      if (lines[0] === '---') {
        for (let i = 1; i < lines.length; i++) {
          if (lines[i] === '---') {
            insertIndex = i + 1;
            break;
          }
        }
      }

      lines.splice(insertIndex, 0, '', reference, '');
      content = lines.join('\n');
      fs.writeFileSync(claudePath, content);
    }
  } else {
    // Create minimal CLAUDE.md with reference
    const minimalCLAUDE = `# CLAUDE.md

${reference}

This file provides instructions for Claude Code when working with this codebase.
`;
    fs.writeFileSync(claudePath, minimalCLAUDE);
  }
}

function initializeStateFiles() {
  console.log(color('Initializing state files...', colors.cyan));

  // Set environment variable so shared_state can find project root
  process.env.CLAUDE_PROJECT_DIR = PROJECT_ROOT;

  // Import and call loadState/loadConfig from shared_state
  const sharedStatePath = path.join(PROJECT_ROOT, 'sessions', 'hooks', 'shared_state.js');

  if (!fs.existsSync(sharedStatePath)) {
    console.log(color('⚠️  Could not find shared_state.js after installation', colors.yellow));
    process.exit(1);
  }

  const { loadState, loadConfig } = require(sharedStatePath);

  // These functions create the files if they don't exist
  loadState();
  loadConfig();

  // Verify files were created
  const stateFile = path.join(PROJECT_ROOT, 'sessions', 'sessions-state.json');
  const configFile = path.join(PROJECT_ROOT, 'sessions', 'sessions-config.json');

  if (!fs.existsSync(stateFile) || !fs.existsSync(configFile)) {
    console.log(color('⚠️  State files were not created properly', colors.yellow));
    console.log(color('You may need to initialize them manually on first run', colors.yellow));
  }
}

// Utility functions

function copyFile(src, dest) {
  if (fs.existsSync(src)) {
    const destDir = path.dirname(dest);
    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
    }
    fs.copyFileSync(src, dest);

    // Preserve executable permissions on Unix
    if (process.platform !== 'win32') {
      try {
        const stats = fs.statSync(src);
        fs.chmodSync(dest, stats.mode);
      } catch (error) {
        // Ignore chmod errors
      }
    }
  }
}

function copyDirectory(src, dest) {
  if (!fs.existsSync(src)) return;

  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      copyFile(srcPath, destPath);
    }
  }
}

// Run installer
main().catch(error => {
  console.error(color('\n❌ Fatal error:', colors.red), error);
  process.exit(1);
});
