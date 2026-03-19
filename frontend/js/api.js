/**
 * api.js — Shared API helper
 *
 * Every page imports this file to talk to the backend.
 * It handles:
 *   - The base URL (one place to change if the server moves)
 *   - Automatically attaching the auth token to requests
 *   - Consistent error handling
 *
 * Usage example:
 *   const listings = await api.get('/listings/');
 *   const listing  = await api.post('/listings/', { title: '...', price: 100000, ... });
 */

// The URL of our FastAPI backend — set in config.js
// Local:      http://localhost:8000
// Production: your Render URL (update config.js before deploying)
const API_BASE = CONFIG.API_BASE;

const api = {

  /**
   * Make a GET request
   * @param {string} path - e.g. '/listings/' or '/listings/3'
   * @param {object} params - optional query params e.g. { location: 'Phnom Penh', max_price: 300000 }
   */
  async get(path, params = {}) {
    // Build the URL with query parameters if any were passed
    const url = new URL(API_BASE + path);
    Object.entries(params).forEach(([key, val]) => {
      if (val !== '' && val !== null && val !== undefined) {
        url.searchParams.set(key, val);
      }
    });

    const res = await fetch(url, {
      headers: this._headers()
    });

    return this._handle(res);
  },

  /**
   * Make a POST request (create something)
   * @param {string} path
   * @param {object} body - the data to send as JSON
   */
  async post(path, body) {
    const res = await fetch(API_BASE + path, {
      method: 'POST',
      headers: { ...this._headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    return this._handle(res);
  },

  /**
   * Make a POST request with form data (used for login)
   * The login endpoint expects form fields, not JSON
   */
  async postForm(path, formData) {
    const res = await fetch(API_BASE + path, {
      method: 'POST',
      body: new URLSearchParams(formData)  // Sends as form fields
    });

    return this._handle(res);
  },

  /**
   * Make a PUT request (update something)
   * @param {string} path - e.g. '/listings/3'
   * @param {object} body - the fields to update
   */
  async put(path, body) {
    const res = await fetch(API_BASE + path, {
      method: 'PUT',
      headers: { ...this._headers(), 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });

    return this._handle(res);
  },

  /**
   * Make a DELETE request
   * @param {string} path - e.g. '/listings/3'
   */
  async delete(path) {
    const res = await fetch(API_BASE + path, {
      method: 'DELETE',
      headers: this._headers()
    });

    // DELETE returns 204 No Content — no JSON body to parse
    if (res.status === 204) return true;

    return this._handle(res);
  },

  /**
   * Build request headers.
   * If the user is logged in (token in localStorage), include it automatically.
   * This is how we prove to the backend that we're an admin.
   */
  _headers() {
    const token = localStorage.getItem('nestkh_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  },

  /**
   * Handle the response — parse JSON or throw an error with a helpful message.
   */
  async _handle(res) {
    if (res.ok) {
      // Some responses have no body (e.g. 204), so we check before parsing
      const text = await res.text();
      return text ? JSON.parse(text) : null;
    }

    // If the request failed, try to get the error message from the response
    let detail = `Request failed (${res.status})`;
    try {
      const err = await res.json();
      detail = err.detail || detail;
    } catch {}

    // If we get a 401, the token is probably expired — send to login
    if (res.status === 401) {
      localStorage.removeItem('nestkh_token');
      window.location.href = '/frontend/login.html';
    }

    throw new Error(detail);
  }
};

/** Format a number as USD e.g. 320000 → "$320,000" */
function fmt(n) {
  return '$' + Number(n).toLocaleString();
}

/** Facility icons map */
const FAC_ICONS = {
  Wifi: '📶', Parking: '🚗', Pool: '🏊', Gym: '🏋️',
  Security: '🔒', Garden: '🌿', Concierge: '🛎️', Solar: '☀️', Balcony: '🏗️'
};

/** Parse a comma-separated facilities string into an array */
function parseFacilities(str) {
  if (!str) return [];
  return str.split(',').map(f => f.trim()).filter(Boolean);
}
