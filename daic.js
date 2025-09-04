#!/usr/bin/env node
/**
 * DAIC command entry point for npm installations.
 * 
 * This script provides the console command for the daic tool when cc-sessions
 * is installed via npm. It locates the project's .claude directory and toggles
 * the DAIC mode by invoking the Python shared_state module.
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Find project root by looking for .claude directory
 * @returns {string|null} Path to project root or null if not found
 */
function findProjectRoot() {
    let current = process.cwd();
    
    while (current !== path.parse(current).root) {
        if (fs.existsSync(path.join(current, '.claude'))) {
            return current;
        }
        current = path.dirname(current);
    }
    
    return null;
}

/**
 * Main function to toggle DAIC mode
 */
function main() {
    const projectRoot = findProjectRoot();
    
    if (!projectRoot) {
        console.error('[DAIC Error] Could not find .claude directory in current path or parent directories');
        process.exit(1);
    }
    
    const hooksDir = path.join(projectRoot, '.claude', 'hooks');
    
    if (!fs.existsSync(hooksDir)) {
        console.error(`[DAIC Error] Hooks directory not found at ${hooksDir}`);
        process.exit(1);
    }
    
    // Run Python inline to toggle mode
    const pythonCode = `
import sys
sys.path.insert(0, '${hooksDir}')
from shared_state import toggle_daic_mode
mode = toggle_daic_mode()
print('[DAIC] ' + mode)
`;
    
    try {
        // Try python3 first, then python
        let pythonCmd = 'python3';
        try {
            execSync('python3 --version', { stdio: 'ignore' });
        } catch {
            pythonCmd = 'python';
        }
        
        const result = execSync(`${pythonCmd} -c "${pythonCode}"`, {
            encoding: 'utf8',
            stdio: ['pipe', 'pipe', 'pipe']
        });
        
        console.log(result.trim());
        process.exit(0);
    } catch (error) {
        if (error.stderr) {
            console.error(error.stderr);
        } else {
            console.error('[DAIC Error] Failed to toggle mode:', error.message);
        }
        process.exit(1);
    }
}

// Run the main function
main();