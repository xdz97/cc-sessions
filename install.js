#!/usr/bin/env node

/**
 * Claude Code Sessions Framework - Node.js Installer
 * Cross-platform installation script for the Sessions framework
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');
const readline = require('readline');
const { promisify } = require('util');

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m',
  bgRed: '\x1b[41m',
  bgGreen: '\x1b[42m',
  bgYellow: '\x1b[43m',
  bgBlue: '\x1b[44m',
  bgMagenta: '\x1b[45m',
  bgCyan: '\x1b[46m'
};

// Helper to colorize output
const color = (text, colorCode) => `${colorCode}${text}${colors.reset}`;

// Icons and symbols
const icons = {
  check: '✓',
  cross: '✗',
  lock: '🔒',
  unlock: '🔓',
  info: 'ℹ',
  warning: '⚠',
  arrow: '→',
  bullet: '•',
  star: '★'
};

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = promisify(rl.question).bind(rl);

// Paths
const SCRIPT_DIR = __dirname;
let PROJECT_ROOT = process.cwd();

// Check if we're running from npx or in wrong directory
async function detectProjectDirectory() {
  // If running from node_modules or temp npx directory
  if (PROJECT_ROOT.includes('node_modules') || PROJECT_ROOT.includes('.npm')) {
    console.log(color('⚠️  Running from package directory, not project directory.', colors.yellow));
    console.log();
    const projectPath = await question('Enter the path to your project directory (or press Enter for current directory): ');
    if (projectPath) {
      PROJECT_ROOT = path.resolve(projectPath);
    } else {
      PROJECT_ROOT = process.cwd();
    }
    console.log(color(`Using project directory: ${PROJECT_ROOT}`, colors.cyan));
  }
}

// Configuration object to build
const config = {
  developer_name: "the developer",
  trigger_phrases: ["make it so", "run that", "go ahead", "yert"],
  blocked_tools: ["Edit", "Write", "MultiEdit", "NotebookEdit"],
  task_detection: { enabled: true },
  branch_enforcement: { enabled: true }
};

// Check if command exists
function commandExists(command) {
  try {
    if (process.platform === 'win32') {
      // Windows - use 'where' command
      execSync(`where ${command}`, { stdio: 'ignore' });
      return true;
    } else {
      // Unix/Mac - use 'which' command
      execSync(`which ${command}`, { stdio: 'ignore' });
      return true;
    }
  } catch {
    return false;
  }
}

// Check dependencies
async function checkDependencies() {
  console.log(color('Checking dependencies...', colors.cyan));
  
  // Check Python
  const hasPython = commandExists('python3') || commandExists('python');
  if (!hasPython) {
    console.log(color('❌ Python 3 is required but not installed.', colors.red));
    process.exit(1);
  }
  
  // Check pip
  const hasPip = commandExists('pip3') || commandExists('pip');
  if (!hasPip) {
    console.log(color('❌ pip is required but not installed.', colors.red));
    process.exit(1);
  }
  
  // Check Git (warning only)
  if (!commandExists('git')) {
    console.log(color('⚠️  Warning: Not in a git repository. Sessions works best with git.', colors.yellow));
    const answer = await question('Continue anyway? (y/n): ');
    if (answer.toLowerCase() !== 'y') {
      process.exit(1);
    }
  }
}

// Create directory structure
async function createDirectories() {
  console.log(color('Creating directory structure...', colors.cyan));
  
  const dirs = [
    '.claude/hooks',
    '.claude/state',
    '.claude/agents',
    '.claude/commands',
    'sessions/tasks/done',
    'sessions/protocols',
    'sessions/knowledge'
  ];
  
  for (const dir of dirs) {
    await fs.mkdir(path.join(PROJECT_ROOT, dir), { recursive: true });
  }
}

// Install Python dependencies
async function installPythonDeps() {
  console.log(color('Installing Python dependencies...', colors.cyan));
  try {
    const pipCommand = commandExists('pip3') ? 'pip3' : 'pip';
    execSync(`${pipCommand} install tiktoken --quiet`, { stdio: 'ignore' });
  } catch (error) {
    console.log(color('⚠️  Could not install tiktoken. You may need to install it manually.', colors.yellow));
  }
}

// Copy files with proper permissions
async function copyFiles() {
  console.log(color('Installing hooks...', colors.cyan));
  const hookFiles = await fs.readdir(path.join(SCRIPT_DIR, 'cc_sessions/hooks'));
  for (const file of hookFiles) {
    if (file.endsWith('.py')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'cc_sessions/hooks', file),
        path.join(PROJECT_ROOT, '.claude/hooks', file)
      );
      if (process.platform !== 'win32') {
        await fs.chmod(path.join(PROJECT_ROOT, '.claude/hooks', file), 0o755);
      }
    }
  }
  
  console.log(color('Installing protocols...', colors.cyan));
  const protocolFiles = await fs.readdir(path.join(SCRIPT_DIR, 'cc_sessions/protocols'));
  for (const file of protocolFiles) {
    if (file.endsWith('.md')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'cc_sessions/protocols', file),
        path.join(PROJECT_ROOT, 'sessions/protocols', file)
      );
    }
  }
  
  console.log(color('Installing agent definitions...', colors.cyan));
  const agentFiles = await fs.readdir(path.join(SCRIPT_DIR, 'cc_sessions/agents'));
  for (const file of agentFiles) {
    if (file.endsWith('.md')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'cc_sessions/agents', file),
        path.join(PROJECT_ROOT, '.claude/agents', file)
      );
    }
  }
  
  console.log(color('Installing templates...', colors.cyan));
  await fs.copyFile(
    path.join(SCRIPT_DIR, 'cc_sessions/templates/TEMPLATE.md'),
    path.join(PROJECT_ROOT, 'sessions/tasks/TEMPLATE.md')
  );
  
  console.log(color('Installing commands...', colors.cyan));
  const commandFiles = await fs.readdir(path.join(SCRIPT_DIR, 'cc_sessions/commands'));
  for (const file of commandFiles) {
    if (file.endsWith('.md')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'cc_sessions/commands', file),
        path.join(PROJECT_ROOT, '.claude/commands', file)
      );
    }
  }
  
  // Copy knowledge files if they exist
  const knowledgePath = path.join(SCRIPT_DIR, 'cc_sessions/knowledge/claude-code');
  try {
    await fs.access(knowledgePath);
    console.log(color('Installing Claude Code knowledge base...', colors.cyan));
    await copyDir(knowledgePath, path.join(PROJECT_ROOT, 'sessions/knowledge/claude-code'));
  } catch {
    // Knowledge files don't exist, skip
  }
}

// Recursive directory copy
async function copyDir(src, dest) {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      await copyDir(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

// Install daic command
async function installDaicCommand() {
  console.log(color('Installing daic command...', colors.cyan));
  
  if (process.platform === 'win32') {
    // Windows installation
    const daicCmdSource = path.join(SCRIPT_DIR, 'cc_sessions/scripts/daic.cmd');
    const daicPs1Source = path.join(SCRIPT_DIR, 'cc_sessions/scripts/daic.ps1');
    
    // Install to user's local directory
    const localBin = path.join(process.env.USERPROFILE || process.env.HOME, 'AppData', 'Local', 'cc-sessions', 'bin');
    await fs.mkdir(localBin, { recursive: true });
    
    try {
      // Copy .cmd script
      await fs.access(daicCmdSource);
      const daicCmdDest = path.join(localBin, 'daic.cmd');
      await fs.copyFile(daicCmdSource, daicCmdDest);
      console.log(color(`  ✓ Installed daic.cmd to ${localBin}`, colors.green));
    } catch {
      console.log(color('  ⚠️ daic.cmd script not found', colors.yellow));
    }
    
    try {
      // Copy .ps1 script
      await fs.access(daicPs1Source);
      const daicPs1Dest = path.join(localBin, 'daic.ps1');
      await fs.copyFile(daicPs1Source, daicPs1Dest);
      console.log(color(`  ✓ Installed daic.ps1 to ${localBin}`, colors.green));
    } catch {
      console.log(color('  ⚠️ daic.ps1 script not found', colors.yellow));
    }
    
    console.log(color(`  ℹ Add ${localBin} to your PATH to use 'daic' command`, colors.yellow));
  } else {
    // Unix/Mac installation
    const daicSource = path.join(SCRIPT_DIR, 'cc_sessions/scripts/daic');
    const daicDest = '/usr/local/bin/daic';
    
    try {
      await fs.copyFile(daicSource, daicDest);
      await fs.chmod(daicDest, 0o755);
    } catch (error) {
      if (error.code === 'EACCES') {
        console.log(color('⚠️  Cannot write to /usr/local/bin. Trying with sudo...', colors.yellow));
        try {
          execSync(`sudo cp ${daicSource} ${daicDest}`, { stdio: 'inherit' });
          execSync(`sudo chmod +x ${daicDest}`, { stdio: 'inherit' });
        } catch {
          console.log(color('⚠️  Could not install daic command globally. You can run it locally from .claude/scripts/', colors.yellow));
        }
      }
    }
  }
}

// Interactive menu with keyboard navigation
async function interactiveMenu(items, options = {}) {
  const {
    title = 'Select an option',
    multiSelect = false,
    selectedItems = new Set(),
    formatItem = (item, selected) => item
  } = options;
  
  let currentIndex = 0;
  let selected = new Set(selectedItems);
  let done = false;
  
  // Hide cursor
  process.stdout.write('\x1B[?25l');
  
  const renderMenu = () => {
    // Clear previous menu
    console.clear();
    
    // Render title
    if (title) {
      console.log(title);
    }
    
    // Render items
    items.forEach((item, index) => {
      const isSelected = selected.has(item);
      const isCurrent = index === currentIndex;
      
      let prefix = '  ';
      if (isCurrent) {
        prefix = color('▶ ', colors.cyan);
      }
      
      console.log(prefix + formatItem(item, isSelected, isCurrent));
    });
  };
  
  return new Promise((resolve) => {
    renderMenu();
    
    // Set raw mode for key input
    readline.emitKeypressEvents(process.stdin);
    if (process.stdin.setRawMode) {
      process.stdin.setRawMode(true);
    }
    process.stdin.resume();
    
    const keyHandler = (str, key) => {
      if (key) {
        if (key.name === 'up') {
          currentIndex = (currentIndex - 1 + items.length) % items.length;
          renderMenu();
        } else if (key.name === 'down') {
          currentIndex = (currentIndex + 1) % items.length;
          renderMenu();
        } else if (key.name === 'space' && multiSelect) {
          const item = items[currentIndex];
          if (selected.has(item)) {
            selected.delete(item);
          } else {
            selected.add(item);
          }
          renderMenu();
        } else if (key.name === 'return') {
          done = true;
          // Restore terminal
          if (process.stdin.setRawMode) {
            process.stdin.setRawMode(false);
          }
          process.stdin.removeListener('keypress', keyHandler);
          process.stdout.write('\x1B[?25h'); // Show cursor
          console.clear();
          
          // Resume stdin for subsequent prompts (don't pause!)
          process.stdin.resume();
          
          if (multiSelect) {
            resolve(selected);
          } else {
            resolve(items[currentIndex]);
          }
        } else if (key.ctrl && key.name === 'c') {
          // Handle Ctrl+C
          if (process.stdin.setRawMode) {
            process.stdin.setRawMode(false);
          }
          process.stdin.pause();
          process.stdout.write('\x1B[?25h'); // Show cursor
          process.exit(0);
        }
      }
    };
    
    process.stdin.on('keypress', keyHandler);
  });
}

// Tool blocking menu
async function configureToolBlocking() {
  const allTools = [
    { name: 'Edit', description: 'Edit existing files', defaultBlocked: true },
    { name: 'Write', description: 'Create new files', defaultBlocked: true },
    { name: 'MultiEdit', description: 'Multiple edits in one operation', defaultBlocked: true },
    { name: 'NotebookEdit', description: 'Edit Jupyter notebooks', defaultBlocked: true },
    { name: 'Bash', description: 'Run shell commands', defaultBlocked: false },
    { name: 'Read', description: 'Read file contents', defaultBlocked: false },
    { name: 'Grep', description: 'Search file contents', defaultBlocked: false },
    { name: 'Glob', description: 'Find files by pattern', defaultBlocked: false },
    { name: 'LS', description: 'List directory contents', defaultBlocked: false },
    { name: 'WebSearch', description: 'Search the web', defaultBlocked: false },
    { name: 'WebFetch', description: 'Fetch web content', defaultBlocked: false },
    { name: 'Task', description: 'Launch specialized agents', defaultBlocked: false }
  ];
  
  // Initialize blocked tools
  const initialBlocked = new Set(config.blocked_tools.map(name => 
    allTools.find(t => t.name === name)
  ).filter(Boolean));
  
  const title = `${color('╭───────────────────────────────────────────────────────────────╮', colors.cyan)}
${color('│              Tool Blocking Configuration                      │', colors.cyan)}
${color('├───────────────────────────────────────────────────────────────┤', colors.cyan)}
${color('│   ↑/↓: Navigate   SPACE: Toggle   ENTER: Save & Continue      │', colors.dim)}
${color('│     Tools marked with 🔒 are blocked in discussion mode       │', colors.dim)}
${color('╰───────────────────────────────────────────────────────────────╯', colors.cyan)}
`;
  
  const formatItem = (tool, isBlocked, isCurrent) => {
    const icon = isBlocked ? icons.lock : icons.unlock;
    const status = isBlocked ? color('[BLOCKED]', colors.red) : color('[ALLOWED]', colors.green);
    const toolColor = isCurrent ? colors.bright : (isBlocked ? colors.yellow : colors.white);
    
    return `${icon} ${color(tool.name.padEnd(15), toolColor)} - ${tool.description.padEnd(30)} ${status}`;
  };
  
  const selectedTools = await interactiveMenu(allTools, {
    title,
    multiSelect: true,
    selectedItems: initialBlocked,
    formatItem
  });
  
  config.blocked_tools = Array.from(selectedTools).map(t => t.name);
  console.log(color(`\n  ${icons.check} Tool blocking configuration saved`, colors.green));
}

// Interactive configuration
async function configure() {
  console.log();
  console.log(color('╔═══════════════════════════════════════════════════════════════╗', colors.bright + colors.cyan));
  console.log(color('║                    CONFIGURATION SETUP                        ║', colors.bright + colors.cyan));
  console.log(color('╚═══════════════════════════════════════════════════════════════╝', colors.bright + colors.cyan));
  console.log();
  
  let statuslineInstalled = false;
  
  // Developer name section
  console.log(color(`\n${icons.star} DEVELOPER IDENTITY`, colors.bright + colors.magenta));
  console.log(color('─'.repeat(60), colors.dim));
  console.log(color('  Claude will use this name when addressing you in sessions', colors.dim));
  console.log();
  
  const name = await question(color('  Your name: ', colors.cyan));
  if (name) {
    config.developer_name = name;
    console.log(color(`  ${icons.check} Hello, ${name}!`, colors.green));
  }
  
  // Statusline installation section
  console.log(color(`\n\n${icons.star} STATUSLINE INSTALLATION`, colors.bright + colors.magenta));
  console.log(color('─'.repeat(60), colors.dim));
  console.log(color('  Real-time status display in Claude Code showing:', colors.white));
  console.log(color(`    ${icons.bullet} Current task and DAIC mode`, colors.cyan));
  console.log(color(`    ${icons.bullet} Token usage with visual progress bar`, colors.cyan));
  console.log(color(`    ${icons.bullet} Modified file counts`, colors.cyan));
  console.log(color(`    ${icons.bullet} Open task count`, colors.cyan));
  console.log();
  
  const installStatusline = await question(color('  Install statusline? (y/n): ', colors.cyan));
  
  if (installStatusline.toLowerCase() === 'y') {
    const statuslineSource = path.join(SCRIPT_DIR, 'cc_sessions/scripts/statusline-script.sh');
    try {
      await fs.access(statuslineSource);
      console.log(color('  Installing statusline script...', colors.dim));
      await fs.copyFile(statuslineSource, path.join(PROJECT_ROOT, '.claude/statusline-script.sh'));
      await fs.chmod(path.join(PROJECT_ROOT, '.claude/statusline-script.sh'), 0o755);
      statuslineInstalled = true;
      console.log(color(`  ${icons.check} Statusline installed successfully`, colors.green));
    } catch {
      console.log(color(`  ${icons.warning} Statusline script not found in package`, colors.yellow));
    }
  }
  
  // DAIC trigger phrases section
  console.log(color(`\n\n${icons.star} DAIC WORKFLOW CONFIGURATION`, colors.bright + colors.magenta));
  console.log(color('─'.repeat(60), colors.dim));
  console.log(color('  The DAIC system enforces discussion before implementation.', colors.white));
  console.log(color('  Trigger phrases tell Claude when you\'re ready to proceed.', colors.white));
  console.log();
  console.log(color('  Default triggers:', colors.cyan));
  config.trigger_phrases.forEach(phrase => {
    console.log(color(`    ${icons.arrow} "${phrase}"`, colors.green));
  });
  console.log();
  console.log(color('  Hint: Common additions: "implement it", "do it", "proceed"', colors.dim));
  console.log();
  
  // Allow adding multiple custom trigger phrases
  let addingTriggers = true;
  while (addingTriggers) {
    const customTrigger = await question(color('  Add custom trigger phrase (Enter to skip): ', colors.cyan));
    if (customTrigger) {
      config.trigger_phrases.push(customTrigger);
      console.log(color(`  ${icons.check} Added: "${customTrigger}"`, colors.green));
    } else {
      addingTriggers = false;
    }
  }
  
  // API Mode configuration
  console.log(color(`\n\n${icons.star} THINKING BUDGET CONFIGURATION`, colors.bright + colors.magenta));
  console.log(color('─'.repeat(60), colors.dim));
  console.log(color('  Token usage is not much of a concern with Claude Code Max', colors.white));
  console.log(color('  plans, especially the $200 tier. But API users are often', colors.white));
  console.log(color('  budget-conscious and want manual control.', colors.white));
  console.log();
  console.log(color('  Sessions was built to preserve tokens across context windows', colors.cyan));
  console.log(color('  but uses saved tokens to enable \'ultrathink\' - Claude\'s', colors.cyan));
  console.log(color('  maximum thinking budget - on every interaction for best results.', colors.cyan));
  console.log();
  console.log(color('  • Max users (recommended): Automatic ultrathink every message', colors.dim));
  console.log(color('  • API users: Manual control with [[ ultrathink ]] when needed', colors.dim));
  console.log();
  console.log(color('  You can toggle this anytime with: /api-mode', colors.dim));
  console.log();
  
  const enableUltrathink = await question(color('  Enable automatic ultrathink for best performance? (y/n): ', colors.cyan));
  if (enableUltrathink.toLowerCase() === 'y' || enableUltrathink.toLowerCase() === 'yes') {
    config.api_mode = false;
    console.log(color(`  ${icons.check} Max mode - ultrathink enabled for best performance`, colors.green));
  } else {
    config.api_mode = true;
    console.log(color(`  ${icons.check} API mode - manual ultrathink control (use [[ ultrathink ]])`, colors.green));
  }
  
  // Advanced configuration
  console.log(color(`\n\n${icons.star} ADVANCED OPTIONS`, colors.bright + colors.magenta));
  console.log(color('─'.repeat(60), colors.dim));
  console.log(color('  Configure tool blocking, task prefixes, and more', colors.white));
  console.log();
  
  const advanced = await question(color('  Configure advanced options? (y/n): ', colors.cyan));
  
  if (advanced.toLowerCase() === 'y') {
    await configureToolBlocking();
    
    // Task prefix configuration
    console.log(color(`\n\n${icons.star} TASK PREFIX CONFIGURATION`, colors.bright + colors.magenta));
    console.log(color('─'.repeat(60), colors.dim));
    console.log(color('  Task prefixes organize work by priority and type', colors.white));
    console.log();
    console.log(color('  Current prefixes:', colors.cyan));
    console.log(color(`    ${icons.arrow} h- (high priority)`, colors.white));
    console.log(color(`    ${icons.arrow} m- (medium priority)`, colors.white));
    console.log(color(`    ${icons.arrow} l- (low priority)`, colors.white));
    console.log(color(`    ${icons.arrow} ?- (investigate/research)`, colors.white));
    console.log();
    
    const customizePrefixes = await question(color('  Customize task prefixes? (y/n): ', colors.cyan));
    if (customizePrefixes.toLowerCase() === 'y') {
      const high = await question(color('  High priority prefix [h-]: ', colors.cyan)) || 'h-';
      const med = await question(color('  Medium priority prefix [m-]: ', colors.cyan)) || 'm-';
      const low = await question(color('  Low priority prefix [l-]: ', colors.cyan)) || 'l-';
      const inv = await question(color('  Investigate prefix [?-]: ', colors.cyan)) || '?-';
      
      config.task_prefixes = {
        priority: [high, med, low, inv]
      };
      
      console.log(color(`  ${icons.check} Task prefixes updated`, colors.green));
    }
  }
  
  return { statuslineInstalled };
}

// Save configuration
async function saveConfig(installStatusline = false) {
  console.log(color('Creating configuration...', colors.cyan));
  
  await fs.writeFile(
    path.join(PROJECT_ROOT, 'sessions/sessions-config.json'),
    JSON.stringify(config, null, 2)
  );
  
  // Create or update .claude/settings.json with hooks configuration
  const settingsPath = path.join(PROJECT_ROOT, '.claude/settings.json');
  let settings = {};
  
  // Check if settings.json already exists
  try {
    const existingSettings = await fs.readFile(settingsPath, 'utf-8');
    settings = JSON.parse(existingSettings);
    console.log(color('Found existing settings.json, merging sessions hooks...', colors.cyan));
  } catch {
    console.log(color('Creating new settings.json with sessions hooks...', colors.cyan));
  }
  
  // Define the sessions hooks
  const sessionsHooks = {
    UserPromptSubmit: [
      {
        hooks: [
          {
            type: "command",
            command: "$CLAUDE_PROJECT_DIR/.claude/hooks/user-messages.py"
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
            command: "$CLAUDE_PROJECT_DIR/.claude/hooks/sessions-enforce.py"
          }
        ]
      },
      {
        matcher: "Task",
        hooks: [
          {
            type: "command",
            command: "$CLAUDE_PROJECT_DIR/.claude/hooks/task-transcript-link.py"
          }
        ]
      }
    ],
    PostToolUse: [
      {
        hooks: [
          {
            type: "command",
            command: "$CLAUDE_PROJECT_DIR/.claude/hooks/post-tool-use.py"
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
            command: "$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.py"
          }
        ]
      }
    ]
  };
  
  // Merge hooks (sessions hooks take precedence)
  if (!settings.hooks) {
    settings.hooks = {};
  }
  
  // Merge each hook type
  for (const [hookType, hookConfig] of Object.entries(sessionsHooks)) {
    if (!settings.hooks[hookType]) {
      settings.hooks[hookType] = hookConfig;
    } else {
      // Append sessions hooks to existing ones
      settings.hooks[hookType] = [...settings.hooks[hookType], ...hookConfig];
    }
  }
  
  // Add statusline if requested
  if (installStatusline) {
    settings.statusLine = {
      type: "command",
      command: "$CLAUDE_PROJECT_DIR/.claude/statusline-script.sh",
      padding: 0
    };
  }
  
  // Save the updated settings
  await fs.writeFile(settingsPath, JSON.stringify(settings, null, 2));
  console.log(color('✅ Sessions hooks configured in settings.json', colors.green));
  
  // Initialize DAIC state
  await fs.writeFile(
    path.join(PROJECT_ROOT, '.claude/state/daic-mode.json'),
    JSON.stringify({ mode: "discussion" }, null, 2)
  );
  
  // Create initial task state
  const currentDate = new Date().toISOString().split('T')[0];
  await fs.writeFile(
    path.join(PROJECT_ROOT, '.claude/state/current_task.json'),
    JSON.stringify({
      task: null,
      branch: null,
      services: [],
      updated: currentDate
    }, null, 2)
  );
}

// CLAUDE.md integration
async function setupClaudeMd() {
  console.log();
  console.log(color('═══════════════════════════════════════════', colors.bright));
  console.log(color('         CLAUDE.md Integration', colors.bright));
  console.log(color('═══════════════════════════════════════════', colors.bright));
  console.log();
  
  // Check for existing CLAUDE.md
  try {
    await fs.access(path.join(PROJECT_ROOT, 'CLAUDE.md'));
    
    // File exists, preserve it and add sessions as separate file
    console.log(color('CLAUDE.md already exists, preserving your project-specific rules...', colors.cyan));
    
    // Copy CLAUDE.sessions.md as separate file
    await fs.copyFile(
      path.join(SCRIPT_DIR, 'cc_sessions/templates/CLAUDE.sessions.md'),
      path.join(PROJECT_ROOT, 'CLAUDE.sessions.md')
    );
    
    // Check if it already includes sessions
    const content = await fs.readFile(path.join(PROJECT_ROOT, 'CLAUDE.md'), 'utf-8');
    if (!content.includes('@CLAUDE.sessions.md')) {
      console.log(color('Adding sessions include to existing CLAUDE.md...', colors.cyan));
      
      const addition = '\n## Sessions System Behaviors\n\n@CLAUDE.sessions.md\n';
      await fs.appendFile(path.join(PROJECT_ROOT, 'CLAUDE.md'), addition);
      
      console.log(color('✅ Added @CLAUDE.sessions.md include to your CLAUDE.md', colors.green));
    } else {
      console.log(color('✅ CLAUDE.md already includes sessions behaviors', colors.green));
    }
  } catch {
    // File doesn't exist, use sessions as CLAUDE.md
    console.log(color('No existing CLAUDE.md found, installing sessions as your CLAUDE.md...', colors.cyan));
    await fs.copyFile(
      path.join(SCRIPT_DIR, 'cc_sessions/templates/CLAUDE.sessions.md'),
      path.join(PROJECT_ROOT, 'CLAUDE.md')
    );
    console.log(color('✅ CLAUDE.md created with complete sessions behaviors', colors.green));
  }
}

// Main installation function
async function install() {
  console.log(color('╔════════════════════════════════════════════╗', colors.bright));
  console.log(color('║            cc-sessions Installer           ║', colors.bright));
  console.log(color('╚════════════════════════════════════════════╝', colors.bright));
  console.log();
  
  // Detect correct project directory
  await detectProjectDirectory();
  
  // Check CLAUDE_PROJECT_DIR
  if (!process.env.CLAUDE_PROJECT_DIR) {
    console.log(color(`⚠️  CLAUDE_PROJECT_DIR not set. Setting it to ${PROJECT_ROOT}`, colors.yellow));
    console.log('   To make this permanent, add to your shell profile:');
    console.log(`   export CLAUDE_PROJECT_DIR="${PROJECT_ROOT}"`);
    console.log();
  }
  
  try {
    await checkDependencies();
    await createDirectories();
    await installPythonDeps();
    await copyFiles();
    await installDaicCommand();
    const { statuslineInstalled } = await configure();
    await saveConfig(statuslineInstalled);
    await setupClaudeMd();
    
    // Success message
    console.log();
    console.log();
    console.log(color('╔═══════════════════════════════════════════════════════════════╗', colors.bright + colors.green));
    console.log(color('║                 🎉 INSTALLATION COMPLETE! 🎉                  ║', colors.bright + colors.green));
    console.log(color('╚═══════════════════════════════════════════════════════════════╝', colors.bright + colors.green));
    console.log();
    
    console.log(color('  Installation Summary:', colors.bright + colors.cyan));
    console.log(color('  ─────────────────────', colors.dim));
    console.log(color(`  ${icons.check} Directory structure created`, colors.green));
    console.log(color(`  ${icons.check} Hooks installed and configured`, colors.green));
    console.log(color(`  ${icons.check} Protocols and agents deployed`, colors.green));
    console.log(color(`  ${icons.check} daic command available globally`, colors.green));
    console.log(color(`  ${icons.check} Configuration saved`, colors.green));
    console.log(color(`  ${icons.check} DAIC state initialized (Discussion mode)`, colors.green));
    
    if (statuslineInstalled) {
      console.log(color(`  ${icons.check} Statusline configured`, colors.green));
    }
    
    console.log();
    
    // Test daic command
    if (commandExists('daic')) {
      console.log(color(`  ${icons.check} daic command verified and working`, colors.green));
    } else {
      console.log(color(`  ${icons.warning} daic command not in PATH`, colors.yellow));
      console.log(color('       Add /usr/local/bin to your PATH', colors.dim));
    }
    
    console.log();
    console.log(color(`  ${icons.star} NEXT STEPS`, colors.bright + colors.magenta));
    console.log(color('  ─────────────', colors.dim));
    console.log();
    console.log(color('  1. Restart Claude Code to activate the sessions hooks', colors.white));
    console.log(color('     ' + icons.arrow + ' Close and reopen Claude Code', colors.dim));
    console.log();
    console.log(color('  2. Create your first task:', colors.white));
    console.log(color('     ' + icons.arrow + ' Tell Claude: "Create a new task"', colors.cyan));
    console.log(color('     ' + icons.arrow + ' Or: "Create a task for implementing feature X"', colors.cyan));
    console.log();
    console.log(color('  3. Start working with the DAIC workflow:', colors.white));
    console.log(color('     ' + icons.arrow + ' Discuss approach first', colors.dim));
    console.log(color('     ' + icons.arrow + ' Say "make it so" to implement', colors.dim));
    console.log(color('     ' + icons.arrow + ' Run "daic" to return to discussion', colors.dim));
    console.log();
    console.log(color('  ──────────────────────────────────────────────────────', colors.dim));
    console.log();
    console.log(color(`  Welcome aboard, ${config.developer_name}! 🚀`, colors.bright + colors.cyan));
    
  } catch (error) {
    console.error(color(`❌ Installation failed: ${error.message}`, colors.red));
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Run installation
if (require.main === module) {
  install().catch(error => {
    console.error(color(`❌ Fatal error: ${error}`, colors.red));
    process.exit(1);
  });
}

module.exports = { install };
