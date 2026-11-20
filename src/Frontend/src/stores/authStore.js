import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useAuthStore = defineStore('auth', () => {
    // State
    const token = ref(localStorage.getItem('token') || null);
    
    let parsedUser = null;
    try {
        const storedUser = localStorage.getItem('user');
        if (storedUser && storedUser !== 'undefined') {
            parsedUser = JSON.parse(storedUser);
        }
    } catch (e) {
        localStorage.removeItem('user');
    }
    const user = ref(parsedUser);

    // Getters
    const isAuthenticated = computed(() => !!token.value);
    const isAdmin = computed(() => user.value && user.value.role_id === 1);

    // Actions
    const setAuth = (newToken, newUser) => {
        token.value = newToken;
        user.value = newUser;
        localStorage.setItem('token', newToken);
        localStorage.setItem('user', JSON.stringify(newUser));
    };

    const logout = () => {
        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    };

    return {
        token,
        user,
        isAuthenticated,
        isAdmin,
        setAuth,
        logout
    };
});
