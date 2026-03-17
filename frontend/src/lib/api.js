const API_BASE = 'http://localhost:8000/api/admin';

export const adminAPI = {
  getToken() {
    return localStorage.getItem('admin_token');
  },

  getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.getToken()}`,
    };
  },

  async request(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 401) {
        localStorage.removeItem('admin_token');
        window.location.href = '/admin/login';
      }
      const error = await response.json();
      throw new Error(error.detail || 'API Error');
    }

    return response.json();
  },

  async getProfile() {
    return this.request('/me');
  },

  async login(email, password) {
    return fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(r => r.json());
  },

  async register(email, password, full_name) {
    return fetch(`${API_BASE}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name }),
    }).then(r => r.json());
  },
};