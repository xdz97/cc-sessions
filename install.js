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

  // Check if already installed and backup if needed
  const sessionsDir = path.join(PROJECT_ROOT, 'sessions');
  let backupDir = null;

  if (fs.existsSync(sessionsDir)) {
    // Check if there's actual content to preserve
    const tasksDir = path.join(sessionsDir, 'tasks');
    let hasContent = false;
    if (fs.existsSync(tasksDir)) {
      const checkContent = (dir) => {
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          if (entry.isDirectory()) {
            if (checkContent(path.join(dir, entry.name))) return true;
          } else if (entry.name.endsWith('.md')) {
            return true;
          }
        }
        return false;
      };
      hasContent = checkContent(tasksDir);
    }

    if (!hasContent) {
      console.log(color('🆕 Detected empty sessions directory, treating as fresh install', colors.cyan));
    } else {
      console.log(color('🔍 Detected existing cc-sessions installation', colors.cyan));
      backupDir = createBackup(PROJECT_ROOT);
    }
  }

  console.log(color('\n⚙️  Installing cc-sessions to: ' + PROJECT_ROOT, colors.cyan));
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

    // Restore tasks if this was an update
    if (backupDir) {
      restoreTasks(PROJECT_ROOT, backupDir);
      const relPath = path.relative(PROJECT_ROOT, backupDir);
      console.log(color(`\n📁 Backup saved at: ${relPath}/`, colors.cyan));
      console.log(color('   (Agents backed up for manual restoration if needed)', colors.cyan));
    }

    console.log(color('\n✅ cc-sessions installed successfully!\n', colors.green));
    console.log(color('Next steps:', colors.bold));
    console.log('  1. Restart your Claude Code session (or run /clear)');
    if (backupDir) {
      console.log('  2. Reconfigure settings (or use kickstart onboarding)');
      console.log('  3. Check backup/ for any custom agents you want to restore\n');
    } else {
      console.log('  2. The kickstart onboarding will guide you through setup\n');
    }

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

function createBackup(projectRoot) {
  // Create timestamped backup of tasks and agents before reinstall
  const now = new Date();
  const timestamp = now.toISOString().replace(/[-:]/g, '').split('.')[0].replace('T', '-').slice(0, 15);
  const backupDir = path.join(projectRoot, '.claude', `.backup-${timestamp}`);

  const relPath = path.relative(projectRoot, backupDir);
  console.log(color(`\n💾 Creating backup at ${relPath}/...`, colors.cyan));

  fs.mkdirSync(backupDir, { recursive: true });

  // Backup all task files (includes done/, indexes/, and all task files)
  const tasksSrc = path.join(projectRoot, 'sessions', 'tasks');
  let taskCount = 0;
  if (fs.existsSync(tasksSrc)) {
    const tasksDest = path.join(backupDir, 'tasks');
    copyDirectory(tasksSrc, tasksDest);

    // Count task files for user feedback and verification
    function countTasksInDir(dir) {
      let count = 0;
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          count += countTasksInDir(fullPath);
        } else if (entry.name.endsWith('.md')) {
          count++;
        }
      }
      return count;
    }

    taskCount = countTasksInDir(tasksSrc);
    const backedUpCount = countTasksInDir(tasksDest);

    if (taskCount !== backedUpCount) {
      console.log(color(`   ✗ Backup verification failed: ${backedUpCount}/${taskCount} files backed up`, colors.red));
      throw new Error('Backup verification failed - aborting to prevent data loss');
    }

    console.log(color(`   ✓ Backed up ${taskCount} task files`, colors.green));
  }

  // Backup all agents
  const agentsSrc = path.join(projectRoot, '.claude', 'agents');
  let agentCount = 0;
  if (fs.existsSync(agentsSrc)) {
    const agentsDest = path.join(backupDir, 'agents');
    copyDirectory(agentsSrc, agentsDest);

    const agentFiles = fs.readdirSync(agentsSrc).filter(f => f.endsWith('.md'));
    const backedUpAgents = fs.readdirSync(agentsDest).filter(f => f.endsWith('.md'));
    agentCount = agentFiles.length;

    if (agentCount !== backedUpAgents.length) {
      console.log(color(`   ✗ Backup verification failed: ${backedUpAgents.length}/${agentCount} agents backed up`, colors.red));
      throw new Error('Backup verification failed - aborting to prevent data loss');
    }

    console.log(color(`   ✓ Backed up ${agentCount} agent files`, colors.green));
  }

  return backupDir;
}

function restoreTasks(projectRoot, backupDir) {
  // Restore tasks from backup after installation
  console.log(color('\n♻️  Restoring tasks...', colors.cyan));

  try {
    const tasksBackup = path.join(backupDir, 'tasks');
    if (fs.existsSync(tasksBackup)) {
      const tasksDest = path.join(projectRoot, 'sessions', 'tasks');
      copyDirectory(tasksBackup, tasksDest);

      // Count restored task files
      function countTasksInDir(dir) {
        let count = 0;
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            count += countTasksInDir(fullPath);
          } else if (entry.name.endsWith('.md')) {
            count++;
          }
        }
        return count;
      }

      const taskCount = countTasksInDir(tasksBackup);
      console.log(color(`   ✓ Restored ${taskCount} task files`, colors.green));
    }
  } catch (e) {
    const relPath = path.relative(projectRoot, backupDir);
    console.log(color(`   ✗ Restore failed: ${e.message}`, colors.red));
    console.log(color(`   Your backup is safe at: ${relPath}/`, colors.yellow));
    console.log(color('   Manually copy files from backup/tasks/ to sessions/tasks/', colors.yellow));
    // Don't throw - let user recover manually
  }
}

// Run installer
main().catch(error => {
  console.error(color('\n❌ Fatal error:', colors.red), error);
  process.exit(1);
});
