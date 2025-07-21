#!/usr/bin/env node

// Quick test to verify the deployed startup integration
const { spawn } = require('child_process');

console.log('🧪 Testing deployed startup integration...');

// Run claude-pm but with a fake argument so it doesn't launch Claude
const testProcess = spawn('claude-pm', ['--nonexistent-flag'], {
    stdio: 'pipe'
});

let output = '';

testProcess.stdout.on('data', (data) => {
    output += data.toString();
});

testProcess.stderr.on('data', (data) => {
    output += data.toString();
});

testProcess.on('close', (code) => {
    console.log('📊 Deployed Version Output:');
    console.log('='.repeat(50));
    console.log(output);
    
    // Check for consistency
    const hasSystemInfo = output.includes('📋 Framework CLAUDE.md:');
    const hasStartupInfo = output.includes('📋 Active framework CLAUDE.md:');
    
    if (hasSystemInfo && hasStartupInfo) {
        const systemMatch = output.match(/📋 Framework CLAUDE\.md: ([^\n]+)/);
        const startupMatch = output.match(/📋 Active framework CLAUDE\.md: ([^\n]+)/);
        
        if (systemMatch && startupMatch) {
            console.log('\n🔍 Consistency Check:');
            console.log(`System Info: "${systemMatch[1]}"`);
            console.log(`Startup Info: "${startupMatch[1]}"`);
            
            if (systemMatch[1].trim() === startupMatch[1].trim()) {
                console.log('✅ Both displays are consistent!');
            } else {
                console.log('❌ Displays are inconsistent!');
            }
        }
    } else {
        console.log('⚠️  Could not find both framework CLAUDE.md displays');
    }
});

setTimeout(() => {
    testProcess.kill();
    console.log('Test completed.');
}, 3000);