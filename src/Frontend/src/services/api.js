import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const baseURL = import.meta.env.DEV 
    ? 'http://localhost:8080/api/v1' 
    : '/Backend/api/v1';

const api = axios.create({
    baseURL: baseURL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
});

// Request interceptor for API calls
api.interceptors.request.use(
    config => {
        const authStore = useAuthStore();
        const token = authStore.token;
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Sesión expirada o token inválido: se cierra la sesión y se pide login
api.interceptors.response.use(
    response => response,
    error => {
        if (error.response?.status === 401 && !error.config.url.startsWith('/auth/')) {
            const authStore = useAuthStore();
            authStore.logout();
            window.location.assign('/auth/login');
        }
        return Promise.reject(error);
    }
);

export default api;
