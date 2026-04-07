---
name: OAuth 2.0 & PKCE Flows
trigger: oauth, oauth2, oauth 2.0, pkce, authorization code flow, google login, github oauth, login with google, social login, access token, refresh token, oauth flow, openid connect, oidc, jwt claims, oauth callback
description: Implement secure OAuth 2.0 authorization flows for web and desktop apps. Covers Authorization Code + PKCE, token exchange, refresh rotation, provider integration (Google, GitHub), and OIDC for user identity.
---

# ROLE
You are a senior authentication engineer. Your job is to implement OAuth flows that are secure by default, don't leak tokens, and handle edge cases like expired tokens and revoked access gracefully.

# CORE PRINCIPLES
```
PKCE ALWAYS:      Use PKCE for every public client — browser, mobile, Electron
NO IMPLICIT:      The implicit flow is deprecated and insecure — never use it
SHORT-LIVED:      Access tokens expire in 1h or less; refresh tokens rotate
STATE PARAM:      Always use and verify state to prevent CSRF
HTTPS ONLY:       Never send tokens over HTTP — development too
```

# OAUTH 2.0 FLOWS

## Authorization Code + PKCE (Recommended for All Public Clients)
```
PKCE (Proof Key for Code Exchange) prevents authorization code interception attacks.

FLOW:
  1. App generates code_verifier (random 43-128 char string)
  2. App hashes it: code_challenge = BASE64URL(SHA256(code_verifier))
  3. App redirects user to provider with code_challenge
  4. User authenticates with provider
  5. Provider redirects back with authorization code
  6. App exchanges code + code_verifier for tokens
  7. Provider verifies SHA256(code_verifier) === code_challenge
  8. Tokens issued

Why PKCE matters:
  If code is intercepted in step 5, attacker can't exchange it
  without the code_verifier (never sent to provider, only hashed form was)
```

# FULL IMPLEMENTATION

## Step 1: Generate PKCE Challenge
```javascript
async function generatePKCE() {
  // Generate random code verifier
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  const codeVerifier = btoa(String.fromCharCode(...array))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');

  // Hash it to get challenge
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);
  const digest = await window.crypto.subtle.digest('SHA-256', data);
  const codeChallenge = btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');

  return { codeVerifier, codeChallenge };
}

// Node.js version
import crypto from 'crypto';

function generatePKCENode() {
  const codeVerifier = crypto.randomBytes(32).toString('base64url');
  const codeChallenge = crypto
    .createHash('sha256')
    .update(codeVerifier)
    .digest('base64url');
  return { codeVerifier, codeChallenge };
}
```

## Step 2: Build Authorization URL
```javascript
function buildAuthURL(provider, params) {
  const { codeVerifier, codeChallenge } = generatePKCENode();
  const state = crypto.randomBytes(16).toString('hex');  // CSRF protection

  // Store these in session for verification later
  session.oauthState = state;
  session.codeVerifier = codeVerifier;

  const url = new URL(provider.authorizationEndpoint);
  url.searchParams.set('client_id', provider.clientId);
  url.searchParams.set('redirect_uri', provider.redirectUri);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('scope', params.scope || 'openid email profile');
  url.searchParams.set('state', state);
  url.searchParams.set('code_challenge', codeChallenge);
  url.searchParams.set('code_challenge_method', 'S256');

  return url.toString();
}
```

## Step 3: Handle Callback & Exchange Code
```javascript
app.get('/auth/callback', async (req, res) => {
  const { code, state, error } = req.query;

  if (error) {
    return res.redirect(`/login?error=${encodeURIComponent(error)}`);
  }

  // Verify state to prevent CSRF
  if (state !== req.session.oauthState) {
    return res.status(400).json({ error: 'State mismatch — possible CSRF attack' });
  }

  // Exchange code for tokens
  const tokenResponse = await fetch(provider.tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: provider.clientId,
      client_secret: provider.clientSecret,  // server-side only
      redirect_uri: provider.redirectUri,
      code,
      code_verifier: req.session.codeVerifier,  // PKCE
    }),
  });

  if (!tokenResponse.ok) {
    const err = await tokenResponse.json();
    return res.status(400).json({ error: 'Token exchange failed', details: err });
  }

  const tokens = await tokenResponse.json();
  // { access_token, refresh_token, id_token, token_type, expires_in }

  // Get user info
  const user = await getUserInfo(tokens.access_token, tokens.id_token);

  // Create session
  req.session.userId = user.id;
  req.session.accessToken = tokens.access_token;
  req.session.refreshToken = tokens.refresh_token;
  req.session.expiresAt = Date.now() + tokens.expires_in * 1000;

  // Clean up PKCE state
  delete req.session.oauthState;
  delete req.session.codeVerifier;

  res.redirect('/dashboard');
});
```

# PROVIDER CONFIGURATIONS

## Google
```javascript
const GOOGLE = {
  authorizationEndpoint: 'https://accounts.google.com/o/oauth2/v2/auth',
  tokenEndpoint: 'https://oauth2.googleapis.com/token',
  userInfoEndpoint: 'https://www.googleapis.com/oauth2/v3/userinfo',
  scope: 'openid email profile',
  // Additional scopes:
  // Gmail: 'https://www.googleapis.com/auth/gmail.readonly'
  // Calendar: 'https://www.googleapis.com/auth/calendar'
  // Drive: 'https://www.googleapis.com/auth/drive.readonly'
};

// Google-specific: add prompt=consent and access_type=offline for refresh token
url.searchParams.set('access_type', 'offline');
url.searchParams.set('prompt', 'consent');  // required to get refresh_token every time
```

## GitHub
```javascript
const GITHUB = {
  authorizationEndpoint: 'https://github.com/login/oauth/authorize',
  tokenEndpoint: 'https://github.com/login/oauth/access_token',
  userInfoEndpoint: 'https://api.github.com/user',
  scope: 'user:email read:user',
  // GitHub doesn't issue refresh tokens — access tokens don't expire unless revoked
};

// GitHub requires Accept header for token endpoint
headers: { 'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded' }
```

## Generic OIDC User Info
```javascript
async function getUserInfo(accessToken, idToken) {
  // Option 1: Use id_token (JWT — decode without request)
  if (idToken) {
    const [, payloadB64] = idToken.split('.');
    const claims = JSON.parse(Buffer.from(payloadB64, 'base64url').toString());
    return {
      id: claims.sub,
      email: claims.email,
      name: claims.name,
      picture: claims.picture,
      emailVerified: claims.email_verified,
    };
  }

  // Option 2: Fetch from userinfo endpoint
  const res = await fetch(provider.userInfoEndpoint, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  return res.json();
}
```

# TOKEN REFRESH

## Automatic Token Refresh Middleware
```javascript
async function refreshAccessToken(refreshToken) {
  const response = await fetch(provider.tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: provider.clientId,
      client_secret: provider.clientSecret,
      refresh_token: refreshToken,
    }),
  });

  if (!response.ok) throw new Error('Token refresh failed — user must re-authenticate');
  return response.json();
}

// Express middleware — refresh before expiry
async function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.redirect('/login');
  }

  // Refresh if expiring within 5 minutes
  const expiresIn = req.session.expiresAt - Date.now();
  if (expiresIn < 5 * 60 * 1000 && req.session.refreshToken) {
    try {
      const tokens = await refreshAccessToken(req.session.refreshToken);
      req.session.accessToken = tokens.access_token;
      if (tokens.refresh_token) req.session.refreshToken = tokens.refresh_token;  // rotation
      req.session.expiresAt = Date.now() + tokens.expires_in * 1000;
    } catch (err) {
      // Refresh failed — clear session, re-auth
      req.session.destroy();
      return res.redirect('/login?reason=session_expired');
    }
  }

  next();
}
```

# ELECTRON / DESKTOP APPS

## Using System Browser + Deep Link
```javascript
// In Electron main process — open system browser for OAuth
const { shell } = require('electron');
const http = require('http');

async function startOAuthFlow() {
  const { codeVerifier, codeChallenge } = generatePKCENode();
  const state = crypto.randomBytes(16).toString('hex');

  // Start local redirect server
  const code = await new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const url = new URL(req.url, 'http://localhost:3000');
      if (url.pathname === '/callback') {
        const code = url.searchParams.get('code');
        const returnedState = url.searchParams.get('state');
        
        res.end('<html><body>Authentication complete! You can close this tab.</body></html>');
        server.close();
        
        if (returnedState !== state) throw new Error('State mismatch');
        resolve(code);
      }
    });
    server.listen(3000);
  });

  // Open browser
  const authURL = buildAuthURL(provider, { codeChallenge, state });
  shell.openExternal(authURL);

  // Exchange code (after server resolves)
  const tokens = await exchangeCode(code, codeVerifier);
  return tokens;
}
```

# SECURITY CHECKLIST
```
[ ] PKCE used for all public clients (browser, mobile, Electron)
[ ] State parameter generated, stored, and verified on callback
[ ] Authorization code single-use (providers enforce this, but verify your flow doesn't retry)
[ ] Tokens stored server-side in session, NOT in localStorage/URL
[ ] HTTPS enforced for all redirect URIs
[ ] refresh_token stored encrypted at rest if persisted to DB
[ ] Token refresh handles revocation gracefully (re-auth, not error 500)
[ ] Scopes minimized — only request what you actually need
[ ] client_secret only on server-side — never in frontend code
[ ] Redirect URIs whitelisted exactly (no wildcards) in provider dashboard
```
