// SECURITY TEST FILE - MEDIUM-RISK VIOLATIONS
// This file contains intentional security violations for testing Security Agent detection

const express = require('express');
const session = require('express-session');
const app = express();

// Medium-risk violations - insecure session configuration
const sessionConfig = {
    // Insecure session secret
    secret: 'weak_session_secret',
    
    // Insecure cookie settings
    cookie: {
        secure: false,      // Should be true for HTTPS
        httpOnly: false,    // Should be true to prevent XSS
        sameSite: 'none',   // Should be 'strict' or 'lax'
        maxAge: 86400000,   // 24 hours - too long
        domain: '.example.com' // Too broad
    },
    
    // Insecure session settings
    resave: true,           // Should be false
    saveUninitialized: true, // Should be false
    name: 'sessionid',      // Default name - predictable
    
    // No session store - uses memory (not scalable)
    // store: undefined
};

// Apply insecure session configuration
app.use(session(sessionConfig));

// Insecure session handling patterns
app.post('/login', (req, res) => {
    const { username, password } = req.body;
    
    // Insecure: no rate limiting
    // Insecure: no account lockout
    // Insecure: no CSRF protection
    
    if (authenticateUser(username, password)) {
        // Insecure session data storage
        req.session.user = {
            id: 123,
            username: username,
            isAdmin: true,
            permissions: ['read', 'write', 'delete'],
            sensitiveData: 'secret_user_data',
            creditCard: '1234-5678-9012-3456',
            ssn: '123-45-6789'
        };
        
        // Insecure: storing sensitive data in session
        req.session.password = password;
        req.session.apiKey = 'sk-1234567890abcdef';
        req.session.dbConnection = 'postgresql://user:pass@localhost/db';
        
        res.json({ success: true });
    } else {
        // Insecure: detailed error messages
        res.status(401).json({ 
            error: 'Invalid credentials',
            attempts: req.session.attempts || 0,
            lastAttempt: new Date().toISOString()
        });
    }
});

// Insecure session management
app.get('/admin', (req, res) => {
    // Insecure: no proper session validation
    if (req.session.user) {
        // Insecure: privilege escalation possible
        if (req.query.admin === 'true') {
            req.session.user.isAdmin = true;
        }
        
        res.json({
            user: req.session.user,
            // Insecure: exposing session data
            sessionData: req.session
        });
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
});

// Insecure session destruction
app.post('/logout', (req, res) => {
    // Insecure: not properly destroying session
    req.session.user = null;
    // Should call req.session.destroy()
    
    res.json({ success: true });
});

// Insecure session fixation vulnerability
app.get('/change-password', (req, res) => {
    // Insecure: not regenerating session ID after authentication
    if (req.session.user) {
        // Should call req.session.regenerate()
        res.json({ message: 'Password changed successfully' });
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
});

// Insecure concurrent session handling
app.get('/profile', (req, res) => {
    // Insecure: no concurrent session limits
    // Insecure: no session timeout validation
    
    if (req.session.user) {
        // Insecure: no session activity tracking
        res.json({
            user: req.session.user,
            sessionCreated: req.session.createdAt,
            sessionExpiry: req.session.cookie.expires
        });
    } else {
        res.status(401).json({ error: 'Unauthorized' });
    }
});

// Insecure session data exposure
app.get('/debug/session', (req, res) => {
    // Insecure: exposing complete session data
    res.json({
        sessionId: req.sessionID,
        sessionData: req.session,
        cookie: req.session.cookie,
        store: req.session.store
    });
});

// Insecure session manipulation
app.post('/admin/impersonate', (req, res) => {
    const { targetUserId } = req.body;
    
    // Insecure: allowing session manipulation
    if (req.session.user && req.session.user.isAdmin) {
        req.session.user.id = targetUserId;
        req.session.user.impersonating = true;
        
        res.json({ success: true, message: 'Impersonation started' });
    } else {
        res.status(403).json({ error: 'Forbidden' });
    }
});

// Insecure session storage patterns
const sessionStore = {
    // Insecure: storing sessions in plain text
    sessions: new Map(),
    
    save: function(sessionId, sessionData) {
        // Insecure: no encryption
        this.sessions.set(sessionId, JSON.stringify(sessionData));
    },
    
    get: function(sessionId) {
        // Insecure: no integrity check
        const data = this.sessions.get(sessionId);
        return data ? JSON.parse(data) : null;
    },
    
    destroy: function(sessionId) {
        // Insecure: not securely deleting
        this.sessions.delete(sessionId);
    }
};

// Insecure JWT session alternative
const jwt = require('jsonwebtoken');

function createInsecureJWT(user) {
    // Insecure JWT configuration
    return jwt.sign(
        {
            id: user.id,
            username: user.username,
            isAdmin: user.isAdmin,
            // Insecure: including sensitive data in JWT
            password: user.password,
            apiKey: user.apiKey,
            creditCard: user.creditCard
        },
        'weak_jwt_secret', // Insecure: weak secret
        {
            expiresIn: '30d', // Insecure: too long expiry
            algorithm: 'HS256' // Could be more secure with RS256
        }
    );
}

// Insecure session validation
function validateSession(req, res, next) {
    // Insecure: no proper session validation
    if (req.session && req.session.user) {
        // Insecure: no session timeout check
        // Insecure: no session IP validation
        // Insecure: no session user agent validation
        
        next();
    } else {
        res.status(401).json({ error: 'Invalid session' });
    }
}

// Insecure session cleanup
setInterval(() => {
    // Insecure: not properly cleaning up expired sessions
    console.log('Session cleanup - not implemented');
}, 3600000); // 1 hour

// Insecure session monitoring
app.get('/admin/sessions', (req, res) => {
    // Insecure: exposing all active sessions
    res.json({
        activeSessions: Array.from(sessionStore.sessions.entries()),
        totalSessions: sessionStore.sessions.size
    });
});

// Export insecure session functions
module.exports = {
    sessionConfig,
    sessionStore,
    createInsecureJWT,
    validateSession,
    app
};