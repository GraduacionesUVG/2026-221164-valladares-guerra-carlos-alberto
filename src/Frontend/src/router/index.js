import { createRouter, createWebHistory } from 'vue-router';

import HomeView from '../views/HomeView.vue';
import ChatView from '../views/ChatView.vue';
import AdminDashboardView from '../views/AdminDashboardView.vue';

import { useAuthStore } from '../stores/authStore';

const routes = [
    { path: '/', name: 'Home', component: HomeView },
    { path: '/auth/login', name: 'Login', component: () => import('../views/auth/AuthView.vue') },
    { path: '/auth/signup', name: 'Signup', component: () => import('../views/auth/AuthView.vue') },
    { path: '/chat', name: 'Chat', component: ChatView, meta: { requiresAuth: true } },
    { path: '/dashboard', name: 'Dashboard', component: AdminDashboardView, meta: { requiresAuth: true, requiresAdmin: true } }
];

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior(to, from, savedPosition) {
        if (to.hash) {
            return {
                el: to.hash,
                behavior: 'smooth',
            }
        }
        return { top: 0 }
    }
});

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();
    
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
        next('/auth/login');
    } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
        next('/chat'); // Si no es admin, mándalo al chat
    } else {
        next();
    }
});

export default router;
