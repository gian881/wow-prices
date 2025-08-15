<script setup lang="ts">
import wowLogo from '@/assets/wow-logo.png'

import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import BellIcon from './icons/BellIcon.vue'
import SearchIcon from './icons/SearchIcon.vue'
import Popover from './ui/popover/Popover.vue'
import PopoverContent from './ui/popover/PopoverContent.vue'
import PopoverTrigger from './ui/popover/PopoverTrigger.vue'
import NotificationItem from './NotificationItem.vue'
import type { Notification } from '@/types'

const notifications = ref<Notification[]>([])

async function loadNotifications() {
  try {
    const response = await fetch('http://localhost:8000/notifications')
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    notifications.value = await response.json()
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

function onMessage(event: MessageEvent) {
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data: { action: string; data: { [key: string]: any } } = JSON.parse(event.data)
    if (!data) return
    if (!(data.action == 'new_notification')) return
    notifications.value.unshift(data.data as Notification)
  } catch (error) {
    console.error('Error handling WebSocket message:', error)
  }
}
let ws: WebSocket
function configureWebSocket() {
  ws = new WebSocket('ws://localhost:8000/ws')
  ws.onmessage = onMessage
  ws.onopen = () => {
    console.log('WebSocket connection established')
  }

  ws.onclose = () => {
    console.log('WebSocket connection closed, attempting to reconnect...')
    setTimeout(() => {
      configureWebSocket()
    }, 5000)
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

loadNotifications()
configureWebSocket()
</script>

<template>
  <header class="flex items-center justify-between pt-8">
    <router-link to="/" class="flex items-center gap-4">
      <img :src="wowLogo" alt="World of Warcraft: Ghosts of K'aresh Logo" />
      <h1 class="font-title text-5xl font-bold">WOW Prices</h1>
    </router-link>
    <div class="flex items-center gap-2">
      <input
        type="text"
        placeholder="Pesquisar item..."
        class="bg-midnight-light-100 placeholder:text-light-yellow/75 text-light-yellow min-w-80 rounded-lg px-4 py-2"
        aria-label="Search for items"
      />
      <button
        class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow mr-2 rounded-lg p-2"
      >
        <search-icon class="text-light-yellow" aria-label="Search for items" />
      </button>
      <popover>
        <popover-trigger as="button" class="relative">
          <bell-icon
            :has-notifications="notifications.length > 0"
            class="text-light-yellow"
            aria-label="Notifications"
          />
          <span
            v-if="notifications.length > 0"
            class="absolute min-w-4 rounded-full bg-[#B10000] p-0.5 text-center font-mono text-xs leading-none font-bold"
            :class="{
              'top-1 right-[3px]': notifications.length < 10,
              'top-1 right-px': notifications.length >= 10,
            }"
            >{{ notifications.length }}
          </span>
        </popover-trigger>
        <popover-content
          as="div"
          class="text-light-yellow mt-1 flex max-h-[calc(100vh-122px)] w-[436px] flex-col gap-2 overflow-x-hidden overflow-y-auto rounded-md border-none bg-[#252329] p-4"
          align="end"
        >
          <p v-if="notifications.length === 0" class="text-light-yellow/75 text-center text-sm">
            Nenhuma nova notificação encontrada.
          </p>
          <transition-group name="notifications-list">
            <notification-item
              v-for="notification in notifications"
              :key="notification.id"
              :notification="notification"
              @mark-as-read="
                (id: number) => {
                  notifications = notifications.filter((n) => n.id !== id)
                  loadNotifications()
                }
              "
            />
          </transition-group>
          <!-- <router-link to="/notifications" class="text-light-yellow mt-2 text-center underline"
            >Ver todas as notificações</router-link
          > -->
        </popover-content>
      </popover>
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
