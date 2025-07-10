// SECURITY TEST FILE - CRITICAL VIOLATIONS
// This file contains intentional security violations for testing Security Agent detection

// Critical violations - should trigger automatic veto
const AWS_ACCESS_KEY_ID = 'AKIAIOSFODNN7EXAMPLE';
const AWS_SECRET_ACCESS_KEY = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY';
const github_token = 'ghp_1234567890123456789012345678901234567890';
const api_key = 'sk-1234567890abcdef1234567890abcdef';
const stripe_key = 'sk_test_1234567890abcdef1234567890abcdef';
const mailgun_key = 'key-1234567890abcdef1234567890abcdef';

// Various API key patterns
const generic_api_key = 'AIzaSyD1234567890abcdef1234567890abcdef';
const oauth_token = 'ya29.1234567890abcdef1234567890abcdef';
const bearer_token = 'Bearer 1234567890abcdef1234567890abcdef';

// Environment variables with secrets
process.env.DATABASE_PASSWORD = 'super_secret_password_123';
process.env.JWT_SECRET = 'my_super_secret_jwt_key_12345';
process.env.ENCRYPTION_KEY = 'encryption_key_that_should_not_be_here';

// Configuration with secrets
const config = {
    database: {
        host: 'localhost',
        user: 'admin',
        password: 'admin123',
        port: 5432
    },
    redis: {
        url: 'redis://user:password123@localhost:6379'
    },
    smtp: {
        host: 'smtp.gmail.com',
        auth: {
            user: 'user@gmail.com',
            pass: 'app_password_123'
        }
    }
};

// Hardcoded tokens in comments
// TODO: Replace with actual token: ghp_abcdef1234567890abcdef1234567890abcdef
/* Production API Key: sk-live-abcdef1234567890abcdef1234567890abcdef */

module.exports = config;