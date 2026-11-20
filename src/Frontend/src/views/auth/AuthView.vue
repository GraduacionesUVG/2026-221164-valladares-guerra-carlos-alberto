<template>
  <div class="content page-wrap">
    <NavBar />
    <div class="auth-layout">
      
      <div class="auth-card-slider" :class="{ 'right-panel-active': isSignUp }">
        
        <!-- ======================= -->
        <!--     SIGN UP (LEFT)      -->
        <!-- ======================= -->
        <div class="form-container sign-up-container">
          <form @submit.prevent="handleSignup" class="auth-form">
            <div class="brand auth-brand">
              <div class="sig"><BotMessageSquare :size="24" stroke-width="2.5" /></div>
            </div>
            <h2 style="color: var(--txt-main); margin-bottom: 20px;">Crear Cuenta</h2>
            
            <div class="form-group w-full text-left">
              <label>Nombre Completo</label>
              <div class="input-with-icon">
                <User :size="18" class="input-icon" />
                <input v-model="signupForm.name" type="text" required class="form-control" placeholder="Juan Pérez" />
              </div>
            </div>

            <div class="form-group mt-3 w-full text-left">
              <label>Correo Electrónico</label>
              <div class="input-with-icon">
                <Mail :size="18" class="input-icon" />
                <input v-model="signupForm.email" type="email" required class="form-control" placeholder="juan@ejemplo.com" />
              </div>
            </div>
            
            <div class="form-group mt-3 w-full text-left">
              <label>Contraseña</label>
              <div class="input-with-icon">
                <Lock :size="18" class="input-icon" />
                <input v-model="signupForm.password" type="password" required minlength="8" class="form-control" placeholder="Mínimo 8 caracteres" />
              </div>
            </div>

            <div v-if="error && isSignUp" class="error-box mt-3 w-full">
              <AlertCircle :size="16" /> {{ error }}
            </div>

            <button type="submit" :disabled="isLoading" class="btn primary w-full mt-5 auth-btn">
              {{ isLoading ? 'Creando...' : 'Registrarme' }}
            </button>
          </form>
        </div>

        <!-- ======================= -->
        <!--     SIGN IN (RIGHT)     -->
        <!-- ======================= -->
        <div class="form-container sign-in-container">
          <form @submit.prevent="handleLogin" class="auth-form">
            <div class="brand auth-brand">
              <div class="sig"><BotMessageSquare :size="24" stroke-width="2.5" /></div>
            </div>
            <h2 style="color: var(--txt-main); margin-bottom: 20px;">Iniciar Sesión</h2>
            
            <div class="form-group w-full text-left">
              <label>Correo Electrónico</label>
              <div class="input-with-icon">
                <Mail :size="18" class="input-icon" />
                <input v-model="loginForm.email" type="email" required class="form-control" placeholder="admin@example.com" />
              </div>
            </div>
            
            <div class="form-group mt-4 w-full text-left">
              <label>Contraseña</label>
              <div class="input-with-icon">
                <Lock :size="18" class="input-icon" />
                <input v-model="loginForm.password" type="password" required class="form-control" placeholder="••••••••" />
              </div>
            </div>

            <div v-if="error && !isSignUp" class="error-box mt-4 w-full">
              <AlertCircle :size="16" /> {{ error }}
            </div>

            <button type="submit" :disabled="isLoading" class="btn primary w-full mt-6 auth-btn">
              {{ isLoading ? 'Validando...' : 'Ingresar' }}
            </button>
          </form>
        </div>
        
        <!-- ======================= -->
        <!--     OVERLAY (COVER)     -->
        <!-- ======================= -->
        <div class="overlay-container">
          <div class="overlay">
            
            <div class="overlay-panel overlay-left">
              <h2 class="overlay-title">¡Bienvenido!</h2>
              <p class="overlay-text">Si ya tienes una cuenta con nosotros, por favor inicia sesión.</p>
              <button class="ghost-btn" @click="toggleMode(false)">Inicia Sesión</button>
            </div>
            
            <div class="overlay-panel overlay-right">
              <h2 class="overlay-title">¡Hola, Ciudadano!</h2>
              <p class="overlay-text">Regístrate para hacer consultas ilimitadas a nuestro Asistente IA.</p>
              <button class="ghost-btn" @click="toggleMode(true)">Regístrate</button>
            </div>
            
          </div>
        </div>
        
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { BotMessageSquare, Mail, Lock, User, AlertCircle } from '@lucide/vue';
import NavBar from '../../components/NavBar.vue';
import api from '../../services/api';
import { useAuthStore } from '../../stores/authStore';

const router = useRouter();
const authStore = useAuthStore();

const isSignUp = ref(false);
const isLoading = ref(false);
const error = ref('');

const loginForm = ref({ email: '', password: '' });
const signupForm = ref({ name: '', email: '', password: '' });

const toggleMode = (signUpMode) => {
  error.value = '';
  isSignUp.value = signUpMode;
};

const handleLogin = async () => {
    isLoading.value = true;
    error.value = '';
    try {
        const response = await api.post('/auth/login', {
            email: loginForm.value.email,
            password: loginForm.value.password
        });
        authStore.setAuth(response.data.token, response.data.user);
        router.push('/');
    } catch (err) {
        error.value = err.response?.data?.error || 'Error de conexión con el servidor.';
    } finally {
        isLoading.value = false;
    }
};

const handleSignup = async () => {
    isLoading.value = true;
    error.value = '';
    try {
        const response = await api.post('/auth/register', {
            name: signupForm.value.name,
            email: signupForm.value.email,
            password: signupForm.value.password
        });
        authStore.setAuth(response.data.token, response.data.user);
        router.push('/chat');
    } catch (err) {
        error.value = err.response?.data?.error || 'Error creando la cuenta.';
    } finally {
        isLoading.value = false;
    }
};
</script>

<style scoped>
.page-wrap {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.auth-layout {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* ----- DOUBLE SLIDER CONTAINER ----- */
.auth-card-slider {
  background: rgba(11, 17, 32, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  position: relative;
  overflow: hidden;
  width: 768px;
  max-width: 100%;
  min-height: 520px;
}

.form-container {
  position: absolute;
  top: 0;
  height: 100%;
  transition: all 0.6s ease-in-out;
}

.sign-in-container {
  left: 0;
  width: 50%;
  z-index: 2;
  opacity: 1;
  pointer-events: auto;
  transition: all 0.6s ease-in-out;
}
.auth-card-slider.right-panel-active .sign-in-container {
  transform: translateX(100%);
  opacity: 0;
  pointer-events: none;
}

.sign-up-container {
  left: 0;
  width: 50%;
  opacity: 0;
  pointer-events: none;
  z-index: 1;
  transition: all 0.6s ease-in-out;
}
.auth-card-slider.right-panel-active .sign-up-container {
  transform: translateX(100%);
  opacity: 1;
  pointer-events: auto;
  z-index: 5;
  animation: show 0.6s;
}

@keyframes show {
  0%, 49.99% { opacity: 0; z-index: 1; }
  50%, 100% { opacity: 1; z-index: 5; }
}

/* ----- OVERLAY ----- */
.overlay-container {
  position: absolute;
  top: 0;
  left: 50%;
  width: 50%;
  height: 100%;
  overflow: hidden;
  transition: transform 0.6s ease-in-out;
  z-index: 100;
}
.auth-card-slider.right-panel-active .overlay-container {
  transform: translateX(-100%);
}

.overlay {
  background: linear-gradient(135deg, var(--amber), var(--amber-deep));
  background-repeat: no-repeat;
  background-size: cover;
  background-position: 0 0;
  color: #0f172a; /* Dark text for contrast */
  position: relative;
  left: -100%;
  height: 100%;
  width: 200%;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
}
.auth-card-slider.right-panel-active .overlay {
  transform: translateX(50%);
}

.overlay-panel {
  position: absolute;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 40px;
  text-align: center;
  top: 0;
  height: 100%;
  width: 50%;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
}

.overlay-left {
  transform: translateX(-20%);
}
.auth-card-slider.right-panel-active .overlay-left {
  transform: translateX(0);
}

.overlay-right {
  right: 0;
  transform: translateX(0);
}
.auth-card-slider.right-panel-active .overlay-right {
  transform: translateX(20%);
}

.overlay-title {
  font-weight: 800;
  font-size: 2rem;
  margin-bottom: 15px;
}
.overlay-text {
  font-size: 0.95rem;
  font-weight: 500;
  line-height: 1.5;
  margin-bottom: 30px;
}

/* ----- FORM ELEMENTS ----- */
.auth-form {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  padding: 0 40px;
  height: 100%;
  text-align: center;
}

.auth-brand {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 10px;
}
.sig {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, var(--amber), var(--amber-deep));
  color: #0f172a;
}

.form-group {
  width: 100%;
  display: flex;
  flex-direction: column;
}
.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
  margin-top: 5px;
}
.input-icon {
  position: absolute;
  left: 14px;
  color: var(--txt-dim);
}
.input-with-icon .form-control {
  padding-left: 42px;
  width: 100%;
}
.w-full {
  width: 100%;
}
.text-left {
  text-align: left;
}
.auth-btn {
  padding: 12px;
  font-size: 1rem;
  display: flex;
  justify-content: center;
}
.ghost-btn {
  background-color: transparent;
  border: 2px solid #0f172a;
  color: #0f172a;
  font-family: 'Sora', sans-serif;
  font-weight: bold;
  font-size: 0.9rem;
  padding: 12px 40px;
  border-radius: 25px;
  cursor: pointer;
  transition: transform 80ms ease-in, background 0.3s, color 0.3s;
}
.ghost-btn:hover {
  background: #0f172a;
  color: var(--amber);
}
.ghost-btn:active {
  transform: scale(0.95);
}
/* ----- CELULAR: un formulario a la vez y el cambio de modo debajo ----- */
@media (max-width: 640px) {
  .auth-layout { align-items: flex-start; padding: 16px; }
  .auth-card-slider { display: flex; flex-direction: column; min-height: 0; }
  .form-container,
  .auth-card-slider.right-panel-active .sign-in-container,
  .auth-card-slider.right-panel-active .sign-up-container {
    position: relative; width: 100%; height: auto; transform: none; animation: none;
  }
  .sign-up-container { display: none; }
  .auth-card-slider.right-panel-active .sign-up-container { display: block; }
  .auth-card-slider.right-panel-active .sign-in-container { display: none; }
  .auth-form { padding: 32px 24px; }

  .overlay-container,
  .auth-card-slider.right-panel-active .overlay-container {
    position: relative; left: 0; width: 100%; height: auto; transform: none;
  }
  .overlay,
  .auth-card-slider.right-panel-active .overlay {
    left: 0; width: 100%; transform: none;
  }
  .overlay-panel,
  .auth-card-slider.right-panel-active .overlay-panel {
    position: relative; width: 100%; height: auto; transform: none; padding: 24px;
  }
  .overlay-left { display: none; }
  .auth-card-slider.right-panel-active .overlay-left { display: flex; }
  .auth-card-slider.right-panel-active .overlay-right { display: none; }
  .overlay-title { font-size: 1.4rem; margin-bottom: 8px; }
  .overlay-text { margin-bottom: 16px; }
}

.error-box {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #ef4444;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
