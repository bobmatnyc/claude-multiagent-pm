// SECURITY TEST FILE - HIGH-RISK VIOLATIONS
// This file contains intentional security violations for testing Security Agent detection

// High-risk violations - should trigger conditional veto
const crypto = require('crypto');

// Weak cryptographic algorithms
const md5Hash = crypto.createHash('md5').update('password').digest('hex');
const sha1Hash = crypto.createHash('sha1').update('data').digest('hex');
const md4Hash = crypto.createHash('md4').update('sensitive').digest('hex');

// Insecure random number generation
const weakRandom = Math.random();
const pseudoRandom = crypto.pseudoRandomBytes(16);

// Weak encryption algorithms
const des = crypto.createCipher('des', 'key');
const rc4 = crypto.createCipher('rc4', 'key');

// Insecure key derivation
const simpleKey = crypto.createHash('sha1').update('password').digest();

// Weak password hashing
function hashPassword(password) {
    // Using MD5 for password hashing - INSECURE
    return crypto.createHash('md5').update(password).digest('hex');
}

// Insecure SSL/TLS configuration
const https = require('https');
const insecureOptions = {
    rejectUnauthorized: false,
    secureProtocol: 'SSLv3_method',
    ciphers: 'RC4-SHA:RC4-MD5'
};

// Deprecated crypto functions
const deprecatedCrypto = {
    createCipher: crypto.createCipher,
    createDecipher: crypto.createDecipher,
    pseudoRandomBytes: crypto.pseudoRandomBytes
};

// Insecure certificate validation
process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';

// ECB mode encryption (insecure)
const ecbCipher = crypto.createCipher('aes-128-ecb', 'key');

// Hardcoded initialization vectors
const staticIV = Buffer.from('1234567890123456');
const aes = crypto.createCipheriv('aes-256-cbc', 'key', staticIV);

// Insecure signature verification
function verifySignature(data, signature, publicKey) {
    // Using SHA1 for signature verification - INSECURE
    const verify = crypto.createVerify('SHA1');
    verify.update(data);
    return verify.verify(publicKey, signature);
}

// Weak key generation
const weakKey = crypto.randomBytes(8); // Too short for AES-256
const predictableKey = Buffer.from('0123456789abcdef0123456789abcdef', 'hex');

// Insecure hash comparison (timing attack vulnerable)
function insecureCompare(a, b) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

// Using deprecated crypto algorithms
const sha0Hash = crypto.createHash('sha').update('data').digest('hex');
const md2Hash = crypto.createHash('md2').update('data').digest('hex');

// Insecure random token generation
function generateToken() {
    // Using timestamp + random - predictable
    return Date.now() + Math.floor(Math.random() * 1000);
}

// Weak HMAC usage
const weakHmac = crypto.createHmac('md5', 'secret');

// Export insecure functions
module.exports = {
    hashPassword,
    verifySignature,
    insecureCompare,
    generateToken,
    weakRandom,
    md5Hash,
    sha1Hash
};