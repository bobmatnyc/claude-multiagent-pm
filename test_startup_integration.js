#!/usr/bin/env node

// Test script to verify startup integration without launching Claude

const fs = require('fs');
const path = require('path');

// Import the manageFrameworkClaudeMd function from claude-pm
async function manageFrameworkClaudeMd() {
    const fs = require('fs');
    const path = require('path');
    
    try {
        // Get current working directory
        const cwd = process.cwd();
        
        // Find the framework directory
        let frameworkDir = null;
        const possibleFrameworkPaths = [
            cwd, // If we're already in the framework
            path.join(cwd, 'claude-multiagent-pm'), // If framework is a subdirectory
            path.dirname(cwd) // If we're in a subdirectory of the framework area
        ];
        
        for (const testPath of possibleFrameworkPaths) {
            if (fs.existsSync(path.join(testPath, 'claude_pm')) && 
                fs.existsSync(path.join(testPath, 'framework', 'CLAUDE.md'))) {
                frameworkDir = testPath;
                break;
            }
        }
        
        // Find all CLAUDE.md files
        const claudeMdFiles = [];
        let searchRoot;
        
        if (!frameworkDir) {
            // Not in a framework context, search in broader area
            searchRoot = '/Users/masa/Projects';
        } else {
            // Framework context, search above framework
            searchRoot = path.dirname(frameworkDir);
        }
        
        function findClaudeMdFiles(dir, maxDepth = 3, currentDepth = 0) {
            if (currentDepth >= maxDepth) return;
            
            try {
                const items = fs.readdirSync(dir);
                
                for (const item of items) {
                    const itemPath = path.join(dir, item);
                    const stat = fs.statSync(itemPath);
                    
                    if (stat.isFile() && item === 'CLAUDE.md') {
                        claudeMdFiles.push(itemPath);
                    } else if (stat.isDirectory() && !item.startsWith('.') && 
                              item !== 'node_modules' && item !== '_archive') {
                        findClaudeMdFiles(itemPath, maxDepth, currentDepth + 1);
                    }
                }
            } catch (error) {
                // Skip directories we can't read
            }
        }
        
        findClaudeMdFiles(searchRoot);
        
        
        // Analyze each CLAUDE.md to determine if it's framework-generated
        const frameworkFiles = [];
        const userFiles = [];
        
        for (const filePath of claudeMdFiles) {
            try {
                const content = fs.readFileSync(filePath, 'utf8');
                
                // Framework indicators (be very conservative)
                const frameworkIndicators = [
                    'Claude PM Framework Configuration - Deployment',
                    'CLAUDE_MD_VERSION:',
                    'FRAMEWORK_VERSION:',
                    'AI ASSISTANT ROLE DESIGNATION',
                    'multi-agent orchestrator',
                    'template CLAUDE.md file for the Claude PM Framework',
                    'Deployment Root:',
                    'Generated:'
                ];
                
                // User/project indicators (these make it NOT a framework file)
                const userIndicators = [
                    'project-specific',
                    'custom instructions',
                    'my project',
                    'this project',
                    'application',
                    'repository',
                    'codebase'
                ];
                
                const hasFrameworkIndicators = frameworkIndicators.some(indicator => 
                    content.includes(indicator));
                const hasUserIndicators = userIndicators.some(indicator => 
                    content.toLowerCase().includes(indicator.toLowerCase()));
                
                
                if (hasFrameworkIndicators && !hasUserIndicators) {
                    frameworkFiles.push({
                        path: filePath,
                        relativePath: path.relative(searchRoot, filePath),
                        content: content.substring(0, 200) // First 200 chars for analysis
                    });
                } else {
                    userFiles.push({
                        path: filePath,
                        relativePath: path.relative(searchRoot, filePath)
                    });
                }
            } catch (error) {
                // Skip files we can't read
            }
        }
        
        // Find the top-most directory that should have the framework CLAUDE.md
        const topLevel = searchRoot;
        const targetFrameworkFile = path.join(topLevel, 'CLAUDE.md');
        
        // Check if we have a proper framework CLAUDE.md at the top level
        const hasTopLevelFramework = frameworkFiles.some(f => f.path === targetFrameworkFile);
        
        if (!hasTopLevelFramework) {
            // Check if we have any framework files at other levels
            const activeFrameworkFile = frameworkFiles.length > 0 ? frameworkFiles[0] : null;
            
            return {
                action: 'no_action',
                reason: 'No framework CLAUDE.md at top level (normal)',
                frameworkFiles: frameworkFiles.length,
                userFiles: userFiles.length,
                activeFrameworkFile: activeFrameworkFile ? activeFrameworkFile.relativePath : null
            };
        }
        
        // We have a framework CLAUDE.md at top level, remove any duplicates below it
        const filesToRemove = frameworkFiles.filter(f => f.path !== targetFrameworkFile);
        
        if (filesToRemove.length === 0) {
            return {
                action: 'clean',
                reason: 'Framework CLAUDE.md structure is already clean',
                frameworkFiles: frameworkFiles.length,
                userFiles: userFiles.length,
                topLevelFile: path.relative(searchRoot, targetFrameworkFile)
            };
        }
        
        // Remove duplicate framework files (VERY CAREFULLY)
        const removedFiles = [];
        for (const file of filesToRemove) {
            try {
                // Extra safety check - make sure it's really a framework file
                if (file.content.includes('Claude PM Framework') || 
                    file.content.includes('CLAUDE_MD_VERSION:')) {
                    fs.unlinkSync(file.path);
                    removedFiles.push(file.relativePath);
                }
            } catch (error) {
                console.error(`Warning: Could not remove ${file.path}: ${error.message}`);
            }
        }
        
        return {
            action: 'cleaned',
            reason: `Removed ${removedFiles.length} duplicate framework CLAUDE.md files`,
            removedFiles,
            frameworkFiles: frameworkFiles.length,
            userFiles: userFiles.length,
            topLevelFile: path.relative(searchRoot, targetFrameworkFile)
        };
        
    } catch (error) {
        return {
            action: 'error',
            reason: error.message
        };
    }
}

async function testStartupIntegration() {
    console.log('🧪 Testing Startup Integration - Framework CLAUDE.md Detection');
    console.log('='.repeat(70));
    
    try {
        // Simulate the startup integration
        const frameworkResult = await manageFrameworkClaudeMd();
        
        console.log('\n📊 Framework Management Results:');
        console.log(`   Action: ${frameworkResult.action}`);
        console.log(`   Reason: ${frameworkResult.reason}`);
        console.log(`   Framework files: ${frameworkResult.frameworkFiles}`);
        console.log(`   User files: ${frameworkResult.userFiles}`);
        
        // Show what would be displayed during startup
        console.log('\n🚀 Startup Display Output:');
        if (frameworkResult.action === 'cleaned') {
            console.log(`🧹 Framework cleanup: ${frameworkResult.reason}`);
            if (frameworkResult.removedFiles && frameworkResult.removedFiles.length > 0) {
                console.log(`   Removed files: ${frameworkResult.removedFiles.join(', ')}`);
            }
        } else if (frameworkResult.action === 'error') {
            console.log(`⚠️  Framework cleanup warning: ${frameworkResult.reason}`);
        }
        
        // Show which framework CLAUDE.md is active
        if (frameworkResult.topLevelFile) {
            console.log(`📋 Active framework CLAUDE.md: ${frameworkResult.topLevelFile}`);
        } else if (frameworkResult.activeFrameworkFile) {
            console.log(`📋 Active framework CLAUDE.md: ${frameworkResult.activeFrameworkFile}`);
        } else if (frameworkResult.frameworkFiles === 0) {
            console.log(`📋 Framework CLAUDE.md: None detected (normal for non-framework contexts)`);
        }
        
        console.log('\n✅ Startup integration test completed successfully!');
        
    } catch (error) {
        console.error('❌ Startup integration test failed:', error.message);
    }
}

testStartupIntegration();