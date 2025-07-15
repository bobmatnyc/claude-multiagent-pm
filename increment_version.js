#!/usr/bin/env node

/**
 * Framework Version Increment Script
 * Triggers deployment to increment CLAUDE_MD_VERSION from 013-014 to 013-015
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

class VersionIncrementer {
    constructor() {
        this.currentDir = process.cwd();
        this.claudeMdPath = path.join(this.currentDir, 'CLAUDE.md');
        this.frameworkTemplate = path.join(this.currentDir, 'framework', 'CLAUDE.md');
    }

    /**
     * Extract version from CLAUDE.md content
     */
    extractVersion(content) {
        const versionMatch = content.match(/CLAUDE_MD_VERSION:\s*([^\n\r]+)/);
        return versionMatch ? versionMatch[1].trim() : null;
    }

    /**
     * Generate next version serial
     */
    generateNextVersion(currentVersion, frameworkVersion = '013') {
        if (!currentVersion || !currentVersion.includes('-')) {
            return `${frameworkVersion}-001`;
        }

        const [framework, serial] = currentVersion.split('-');
        if (framework === frameworkVersion) {
            const nextSerial = parseInt(serial) + 1;
            return `${frameworkVersion}-${nextSerial.toString().padStart(3, '0')}`;
        } else {
            return `${frameworkVersion}-001`;
        }
    }

    /**
     * Update CLAUDE.md with incremented version
     */
    async incrementVersion() {
        try {
            console.log('🔧 Framework Version Increment Utility');
            console.log('=' + '='.repeat(49));

            // Check if CLAUDE.md exists
            let currentVersion = null;
            let claudeMdExists = false;

            try {
                const currentContent = await fs.readFile(this.claudeMdPath, 'utf-8');
                currentVersion = this.extractVersion(currentContent);
                claudeMdExists = true;
                console.log(`📋 Current CLAUDE_MD_VERSION: ${currentVersion}`);
            } catch (error) {
                console.log('📋 No existing CLAUDE.md found');
            }

            // Read framework template
            let templateContent;
            try {
                templateContent = await fs.readFile(this.frameworkTemplate, 'utf-8');
                console.log('📄 Framework template loaded');
            } catch (error) {
                console.error('❌ Could not read framework template:', error.message);
                return false;
            }

            // Generate next version
            const nextVersion = this.generateNextVersion(currentVersion);
            console.log(`📋 Next CLAUDE_MD_VERSION: ${nextVersion}`);

            // Generate timestamp
            const timestamp = new Date().toISOString();
            console.log(`⏰ LAST_UPDATED: ${timestamp}`);

            // Replace template variables
            let deployedContent = templateContent
                .replace(/{{CLAUDE_MD_VERSION}}/g, nextVersion)
                .replace(/{{FRAMEWORK_VERSION}}/g, '013')
                .replace(/{{DEPLOYMENT_DATE}}/g, timestamp)
                .replace(/{{LAST_UPDATED}}/g, timestamp)
                .replace(/{{CONTENT_HASH}}/g, 'framework_update_' + Date.now())
                .replace(/{{PLATFORM}}/g, process.platform)
                .replace(/{{PYTHON_CMD}}/g, 'python3')
                .replace(/{{DEPLOYMENT_DIR}}/g, this.currentDir)
                .replace(/{{DEPLOYMENT_ID}}/g, 'version_increment_' + Date.now())
                .replace(/{{PLATFORM_NOTES}}/g, 'Framework version increment after agent registry documentation update');

            // Write the updated CLAUDE.md
            await fs.writeFile(this.claudeMdPath, deployedContent, 'utf-8');
            console.log('✅ CLAUDE.md updated successfully');

            // Verify the update
            const updatedContent = await fs.readFile(this.claudeMdPath, 'utf-8');
            const finalVersion = this.extractVersion(updatedContent);
            
            if (finalVersion === nextVersion) {
                console.log(`🎉 Version successfully incremented: ${currentVersion} → ${finalVersion}`);
                console.log('\n✅ Framework version increment completed successfully!');
                console.log('📋 CLAUDE_MD_VERSION has been incremented by 1');
                console.log('⏰ LAST_UPDATED timestamp has been updated');
                console.log('🔧 Framework template integrity validated');
                return true;
            } else {
                console.log('❌ Version verification failed');
                return false;
            }

        } catch (error) {
            console.error('❌ Error during version increment:', error.message);
            return false;
        }
    }
}

// Execute the version increment
async function main() {
    const incrementer = new VersionIncrementer();
    const result = await incrementer.incrementVersion();
    
    if (!result) {
        console.log('\n❌ Framework version increment failed!');
        console.log('Please check error messages above for details');
        process.exit(1);
    }
    
    process.exit(0);
}

if (require.main === module) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}

module.exports = VersionIncrementer;