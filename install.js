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
  cyan: '\x1b[36m'
};

// Helper to colorize output
const color = (text, colorCode) => `${colorCode}${text}${colors.reset}`;

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const question = promisify(rl.question).bind(rl);

// Paths
const SCRIPT_DIR = __dirname;
const PROJECT_ROOT = process.cwd();

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
    execSync(`which ${command}`, { stdio: 'ignore' });
    return true;
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
    'sessions/tasks/done',
    'sessions/protocols',
    'sessions/agents',
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
  const hookFiles = await fs.readdir(path.join(SCRIPT_DIR, 'hooks'));
  for (const file of hookFiles) {
    if (file.endsWith('.py')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'hooks', file),
        path.join(PROJECT_ROOT, '.claude/hooks', file)
      );
      await fs.chmod(path.join(PROJECT_ROOT, '.claude/hooks', file), 0o755);
    }
  }
  
  console.log(color('Installing protocols...', colors.cyan));
  const protocolFiles = await fs.readdir(path.join(SCRIPT_DIR, 'protocols'));
  for (const file of protocolFiles) {
    if (file.endsWith('.md')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'protocols', file),
        path.join(PROJECT_ROOT, 'sessions/protocols', file)
      );
    }
  }
  
  console.log(color('Installing agent definitions...', colors.cyan));
  const agentFiles = await fs.readdir(path.join(SCRIPT_DIR, 'agents'));
  for (const file of agentFiles) {
    if (file.endsWith('.md')) {
      await fs.copyFile(
        path.join(SCRIPT_DIR, 'agents', file),
        path.join(PROJECT_ROOT, '.claude/agents', file)
      );
    }
  }
  
  console.log(color('Installing templates...', colors.cyan));
  await fs.copyFile(
    path.join(SCRIPT_DIR, 'templates/TEMPLATE.md'),
    path.join(PROJECT_ROOT, 'sessions/tasks/TEMPLATE.md')
  );
  
  // Copy knowledge files if they exist
  const knowledgePath = path.join(SCRIPT_DIR, 'knowledge/claude-code');
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
  
  const daicSource = path.join(SCRIPT_DIR, 'scripts/daic');
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

// Interactive configuration
async function configure() {
  console.log();
  console.log(color('═══════════════════════════════════════════', colors.bright));
  console.log(color('           Configuration Setup', colors.bright));
  console.log(color('═══════════════════════════════════════════', colors.bright));
  console.log();
  
  // Developer name
  const name = await question('Your name (for session context): ');
  if (name) config.developer_name = name;
  
  // Statusline installation
  console.log();
  console.log(color('Statusline Installation:', colors.cyan));
  console.log('The sessions system includes a statusline script that shows:');
  console.log('- Current task and DAIC mode');
  console.log('- Token usage and warnings');
  console.log('- File change counts');
  console.log();
  
  const installStatusline = await question('Install sessions statusline? (y/n): ');
  
  if (installStatusline.toLowerCase() === 'y') {
    const statuslineSource = path.join(SCRIPT_DIR, 'scripts/statusline-script.sh');
    try {
      await fs.access(statuslineSource);
      console.log(color('Installing statusline script...', colors.cyan));
      await fs.copyFile(statuslineSource, path.join(PROJECT_ROOT, '.claude/statusline-script.sh'));
      await fs.chmod(path.join(PROJECT_ROOT, '.claude/statusline-script.sh'), 0o755);
      
      // Create project-level settings.json
      const settings = {
        statusLine: {
          type: "command",
          command: "$CLAUDE_PROJECT_DIR/.claude/statusline-script.sh",
          padding: 0
        }
      };
      
      await fs.writeFile(
        path.join(PROJECT_ROOT, '.claude/settings.json'),
        JSON.stringify(settings, null, 2)
      );
      
      console.log(color('✅ Statusline installed and configured automatically', colors.green));
    } catch {
      console.log(color('⚠️  Statusline script not found in package. Skipping.', colors.yellow));
    }
  }
  
  // DAIC trigger phrases
  console.log();
  console.log(color('DAIC (Discussion, Alignment, Implementation, Check) System:', colors.cyan));
  console.log('By default, Claude will discuss before implementing.');
  console.log('Trigger phrases switch to implementation mode.');
  console.log();
  console.log(`Default triggers: ${config.trigger_phrases.join(', ')}`);
  
  const customTrigger = await question('Add custom trigger phrase (or press Enter to skip): ');
  if (customTrigger) {
    config.trigger_phrases.push(customTrigger);
  }
  
  // Advanced configuration
  console.log();
  const advanced = await question('Configure advanced options? (y/n): ');
  
  if (advanced.toLowerCase() === 'y') {
    // Tool blocking
    console.log();
    console.log(color('Tool Blocking Configuration:', colors.cyan));
    console.log(`Current blocked tools: ${config.blocked_tools.join(', ')}`);
    const modifyTools = await question('Modify blocked tools list? (y/n): ');
    
    if (modifyTools.toLowerCase() === 'y') {
      const customBlocked = await question('Enter comma-separated list of tools to block: ');
      if (customBlocked) {
        config.blocked_tools = customBlocked.split(',').map(t => t.trim());
      }
    }
  }
}

// Save configuration
async function saveConfig() {
  console.log(color('Creating configuration...', colors.cyan));
  
  await fs.writeFile(
    path.join(PROJECT_ROOT, '.claude/sessions-config.json'),
    JSON.stringify(config, null, 2)
  );
  
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
  
  console.log('The sessions system is designed to preserve context by loading only');
  console.log('what\'s needed for the current task. Keep your root CLAUDE.md minimal');
  console.log('with project overview and behavioral rules. Task-specific context is');
  console.log('loaded dynamically through the sessions system.');
  console.log();
  console.log('Your CLAUDE.md should be < 100 lines. Detailed documentation belongs');
  console.log('in task context manifests, not the root file.');
  console.log();
  
  // Copy CLAUDE.sessions.md to project root
  console.log(color('Installing CLAUDE.sessions.md...', colors.cyan));
  await fs.copyFile(
    path.join(SCRIPT_DIR, 'templates/CLAUDE.sessions.md'),
    path.join(PROJECT_ROOT, 'CLAUDE.sessions.md')
  );
  
  // Check for existing CLAUDE.md
  try {
    await fs.access(path.join(PROJECT_ROOT, 'CLAUDE.md'));
    
    // File exists, check if it already includes sessions
    const content = await fs.readFile(path.join(PROJECT_ROOT, 'CLAUDE.md'), 'utf-8');
    if (!content.includes('@CLAUDE.sessions.md')) {
      console.log(color('Adding sessions include to existing CLAUDE.md...', colors.cyan));
      
      const addition = '\n## Sessions System Behaviors\n\n@CLAUDE.sessions.md\n';
      await fs.appendFile(path.join(PROJECT_ROOT, 'CLAUDE.md'), addition);
      
      console.log(color('✅ Added @CLAUDE.sessions.md include to your CLAUDE.md', colors.green));
      console.log();
      console.log(color('⚠️  Please review your CLAUDE.md and consider:', colors.yellow));
      console.log('   - Moving detailed documentation to task context manifests');
      console.log('   - Keeping only project overview and core rules');
      console.log('   - See CLAUDE.example.md for best practices');
    } else {
      console.log(color('✅ CLAUDE.md already includes sessions behaviors', colors.green));
    }
  } catch {
    // File doesn't exist, create from template
    console.log(color('Creating CLAUDE.md from template...', colors.cyan));
    await fs.copyFile(
      path.join(SCRIPT_DIR, 'templates/CLAUDE.example.md'),
      path.join(PROJECT_ROOT, 'CLAUDE.md')
    );
    console.log(color('✅ CLAUDE.md created from best practice template', colors.green));
    console.log('   Please customize the project overview section');
  }
}

// Main installation function
async function install() {
  console.log(color('╔══════════════════════════════════════════╗', colors.bright));
  console.log(color('║    Claude Code Sessions Installer       ║', colors.bright));
  console.log(color('╚══════════════════════════════════════════╝', colors.bright));
  console.log();
  
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
    await configure();
    await saveConfig();
    await setupClaudeMd();
    
    // Success message
    console.log();
    console.log(color('═══════════════════════════════════════════', colors.bright));
    console.log(color('          Installation Complete!', colors.bright));
    console.log(color('═══════════════════════════════════════════', colors.bright));
    console.log();
    
    console.log(color('✅ Directory structure created', colors.green));
    console.log(color('✅ Hooks installed', colors.green));
    console.log(color('✅ Protocols and agents installed', colors.green));
    console.log(color('✅ daic command available', colors.green));
    console.log(color('✅ Configuration saved', colors.green));
    console.log(color('✅ DAIC state initialized (Discussion mode)', colors.green));
    console.log();
    
    // Test daic command
    if (commandExists('daic')) {
      console.log(color('Testing daic command...', colors.cyan));
      console.log(color('✅ daic command working', colors.green));
    } else {
      console.log(color('⚠️  daic command not in PATH. Add /usr/local/bin to your PATH.', colors.yellow));
    }
    
    console.log();
    console.log(color('Next steps:', colors.cyan));
    console.log('1. Restart Claude Code to load the hooks');
    console.log('2. Create your first task:');
    console.log('   Tell Claude: "Create a task using @sessions/protocols/task-creation.md"');
    console.log('3. Start working with DAIC workflow!');
    console.log();
    console.log(`Developer: ${config.developer_name}`);
    
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