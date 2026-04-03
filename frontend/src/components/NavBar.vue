<script setup lang="ts">
import wowLogo from '@/assets/wow-logo.png'
import GeneralSettingsDialog from '@/components/GeneralSettingsDialog.vue'
import NotificationPopover from '@/components/notifications/NotificationPopover.vue'
import { state as websocketState } from '@/services/websocketService'
import { useQueryClient } from '@tanstack/vue-query'
import { watch } from 'vue'
import { RouterLink } from 'vue-router'

const queryClient = useQueryClient()
watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if (
      'action' in newMessage &&
      'data' in newMessage &&
      newMessage.action === 'new_notification'
    ) {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
  },
  { deep: true },
)
</script>

<template>
  <header class="flex items-center justify-between pt-8">
    <router-link to="/" class="flex items-center gap-4">
      <img :src="wowLogo" alt="World of Warcraft: Midnight Logo" />
      <h1 class="font-title text-5xl font-bold">WOW Prices</h1>
    </router-link>
    <div class="flex items-center gap-5">
      <ul class="flex items-center gap-3">
        <li>
          <router-link
            to="/items"
            class="text-accent-white hover:text-accent-400 text-lg transition-colors duration-400 ease-in-out"
            :class="{
              'font-semibold': $route.path === '/items',
            }"
          >
            Itens
          </router-link>
        </li>
        <li>
          <router-link
            to="/week"
            class="text-accent-white hover:text-accent-400 text-lg transition-colors duration-400 ease-in-out"
            :class="{
              'font-semibold': $route.path === '/week',
            }"
          >
            Semana
          </router-link>
        </li>
        <li>
          <router-link
            to="/calculator"
            class="text-accent-white hover:text-accent-400 text-lg transition-colors duration-400 ease-in-out"
            :class="{
              'font-semibold': $route.path === '/calculator',
            }"
          >
            Calculadora
          </router-link>
        </li>
      </ul>
      <div class="flex items-center gap-2">
        <general-settings-dialog />
        <notification-popover />
      </div>
    </div>
  </header>
</template>

<style scoped>
.notifications-list-enter-active,
.notifications-list-leave-active {
  transition: all 300ms ease;
}

.notifications-list-enter-to,
.notifications-list-leave-from {
  opacity: 1;
  transform: translateX(0);
}

.notifications-list-leave-to {
  opacity: 0;
  transform: translateX(400px);
}

.notifications-list-enter-from {
  opacity: 0;
  transform: translateX(-400px);
}
</style>
