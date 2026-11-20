<template>
  <div class="view-panel">
    <div class="page-title flex-between">
      <div>
        <h1>Usuarios y Roles</h1>
        <p>Administra los permisos de acceso al dashboard.</p>
      </div>
      <button class="btn-primary" @click="$emit('new-user')">
        <UserPlus :size="16"/> Nuevo Usuario
      </button>
    </div>
    
    <div class="data-table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Usuario</th>
            <th>Rol</th>
            <th>Estado</th>
            <th>Fecha de Creación</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="5" class="text-center text-dim py-4">Cargando usuarios...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="5" class="text-center text-dim py-4">No hay usuarios registrados.</td>
          </tr>
          <tr v-for="user in users" :key="user.id">
            <td>
              <div class="user-row">
                <div class="avatar-small">{{ user.name.substring(0, 2).toUpperCase() }}</div>
                <div>
                  <b>{{ user.name }}</b>
                  <span>{{ user.email }}</span>
                </div>
              </div>
            </td>
            <td>
              <span :class="['badge', getRoleBadgeColor(user.role_name)]">{{ user.role_name }}</span>
            </td>
            <td><span class="text-dim">Activo</span></td>
            <td><span class="text-dim">{{ new Date(user.created_at).toLocaleDateString() }}</span></td>
            <td><button class="icon-btn-small"><MoreVertical :size="16"/></button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { UserPlus, MoreVertical } from '@lucide/vue';
import api from '../../services/api';

const emit = defineEmits(['new-user']);
const users = ref([]);
const loading = ref(true);

const loadUsers = async () => {
  loading.value = true;
  try {
    const res = await api.get('/users');
    users.value = res.data;
  } catch (error) {
    console.error("Error cargando usuarios:", error);
  } finally {
    loading.value = false;
  }
};

const getRoleBadgeColor = (role) => {
  if (!role) return 'gray';
  const r = role.toLowerCase();
  if (r.includes('admin')) return 'green';
  return 'gray';
};

onMounted(() => {
  loadUsers();
});

// Exponer método para recargar si el parent (Dashboard) lo requiere
defineExpose({ loadUsers });
</script>
