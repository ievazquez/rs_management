/**
 * Servicios de API
 * Funciones para comunicarse con el backend
 */
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Configurar axios
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para agregar token a las peticiones
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Servicios de autenticación
export const authService = {
  login: async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/api/auth/register', userData);
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  }
};

// Servicios de cuentas sociales
export const socialService = {
  getConnectedAccounts: async () => {
    const response = await api.get('/api/social/accounts');
    return response.data;
  },

  getAuthUrl: async (platform) => {
    const response = await api.get(`/api/social/auth-url/${platform}`);
    return response.data;
  },

  connectAccount: async (platform, code, redirectUri) => {
    const response = await api.post('/api/social/connect', {
      platform,
      code,
      redirect_uri: redirectUri
    });
    return response.data;
  },

  disconnectAccount: async (accountId) => {
    const response = await api.delete(`/api/social/disconnect/${accountId}`);
    return response.data;
  },

  getPlatforms: async () => {
    const response = await api.get('/api/social/platforms');
    return response.data;
  }
};

// Servicios de publicaciones
export const postService = {
  getPosts: async (skip = 0, limit = 20) => {
    const response = await api.get(`/api/posts/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getPost: async (postId) => {
    const response = await api.get(`/api/posts/${postId}`);
    return response.data;
  },

  createPost: async (postData) => {
    const response = await api.post('/api/posts/', postData);
    return response.data;
  },

  updatePost: async (postId, postData) => {
    const response = await api.put(`/api/posts/${postId}`, postData);
    return response.data;
  },

  deletePost: async (postId) => {
    const response = await api.delete(`/api/posts/${postId}`);
    return response.data;
  },

  publishPost: async (postId) => {
    const response = await api.post(`/api/posts/${postId}/publish`);
    return response.data;
  }
};

export default api;
