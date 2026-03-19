/**
 * auth.js — Login page logic and auth helpers
 *
 * How login works:
 *   1. User submits username + password
 *   2. We POST to /auth/login
 *   3. Backend returns a JWT token
 *   4. We store the token in localStorage (persists across page loads)
 *   5. We redirect to admin.html
 *
 * On logout:
 *   - We remove the token from localStorage
 *   - Redirect to login.html
 *
 * localStorage is the browser's built-in key-value store.
 * It survives page refreshes but is cleared when the user logs out.
 */

const TOKEN_KEY = 'nestkh_token'; // The key we use in localStorage

/** Handle the login form submission */
async function doLogin(event) {
  event.preventDefault(); // Don't reload the page on form submit

  const btn      = document.getElementById('login-btn');
  const errorDiv = document.getElementById('login-error');

  // Clear previous error and show loading state
  errorDiv.style.display = 'none';
  btn.textContent        = 'Logging in...';
  btn.disabled           = true;

  try {
    // POST to /auth/login with form fields (not JSON)
    const result = await api.postForm('/auth/login', {
      username: document.getElementById('username').value,
      password: document.getElementById('password').value,
    });

    // Store the token in the browser's localStorage
    // From now on, api.js will automatically include this in every request header
    localStorage.setItem(TOKEN_KEY, result.access_token);

    // Redirect to the admin panel
    window.location.href = 'admin.html';

  } catch (err) {
    // Show the error message
    errorDiv.style.display = 'block';
    btn.textContent        = 'Login';
    btn.disabled           = false;
  }
}

/** Call this from any page to log out */
function logout() {
  localStorage.removeItem(TOKEN_KEY);
  window.location.href = 'login.html';
}

/**
 * Redirect to login if not authenticated.
 * Call this at the top of any admin-only page.
 *
 * We check by calling GET /auth/me — if the token is valid, we get
 * the username back. If it's expired or missing, we get a 401 and
 * api.js redirects us to login.html automatically.
 */
async function requireAuth() {
  const token = localStorage.getItem(TOKEN_KEY);

  if (!token) {
    window.location.href = 'login.html';
    return null;
  }

  try {
    const user = await api.get('/auth/me');
    return user; // Returns { username: 'admin' }
  } catch {
    // api.js already handles 401 by redirecting to login.html
    return null;
  }
}

// If we're on the login page and already logged in, skip to admin
if (window.location.pathname.includes('login.html')) {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    window.location.href = 'admin.html';
  }
}
