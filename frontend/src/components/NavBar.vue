<script setup lang="ts">
import wowLogo from '@/assets/wow-logo.png'

import type { Notification } from '@/types'
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import BellIcon from './icons/BellIcon.vue'
import NotificationItem from './NotificationItem.vue'
import Popover from './ui/popover/Popover.vue'
import PopoverContent from './ui/popover/PopoverContent.vue'
import PopoverTrigger from './ui/popover/PopoverTrigger.vue'

const notifications = ref<Notification[]>([])

async function markAsReadAllBelow(id: number) {
  const index = notifications.value.findIndex((n) => n.id === id)
  if (index !== -1) {
    const idsToMarkAsRead = notifications.value.slice(index).map((n) => n.id)
    try {
      const response = await fetch(`http://localhost:8000/notifications/mark-read`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(idsToMarkAsRead),
      })

      if (!response.ok) {
        if (response.status === 500) {
          const errorData = await response.json()
          throw new Error(errorData.message)
        }
        throw new Error()
      }

      notifications.value = notifications.value.filter((n) => !idsToMarkAsRead.includes(n.id))
    } catch (error) {
      console.error('Failed to mark notifications as read:', error)
    }
  }
}

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
      <popover>
        <popover-trigger as="button" class="relative">
          <bell-icon
            :has-notifications="notifications.length > 0"
            class="text-light-yellow"
            aria-label="Notifications"
            filled
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
              @mark-as-read-all-below="markAsReadAllBelow"
            />
          </transition-group>
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
