<script setup lang="ts">
import wowLogo from '@/assets/wow-logo.png'
import GeneralSettingsDialog from '@/components/GeneralSettingsDialog.vue'
import BellIcon from '@/components/icons/BellIcon.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import NotificationItem from '@/components/NotificationItem.vue'
import Popover from '@/components/ui/popover/Popover.vue'
import PopoverContent from '@/components/ui/popover/PopoverContent.vue'
import PopoverTrigger from '@/components/ui/popover/PopoverTrigger.vue'
import { getNotifications, markAllNotificationsAsRead } from '@/services/api/endpoints/notification'
import { state as websocketState } from '@/services/websocketService'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useIntersectionObserver } from '@vueuse/core'
import { computed, ref, useTemplateRef, watch } from 'vue'
import { RouterLink } from 'vue-router'
import CheckIcon from './icons/CheckIcon.vue'

const unreadNotificationsCount = ref(0)
const isSettingsOpen = ref(false)
const showReadNotifications = ref(false)
const queryClient = useQueryClient()

const { data, hasNextPage, fetchNextPage } = useInfiniteQuery({
  staleTime: 1000 * 60, // 1 minute
  queryKey: ['notifications', showReadNotifications],
  queryFn: async ({ pageParam }) => {
    const { data: notifications, meta } = await getNotifications(
      !showReadNotifications.value,
      pageParam,
    )
    return { notifications, meta }
  },
  initialPageParam: 1,

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  getNextPageParam: (lastPage, _) => lastPage.meta.next_page,
})

const target = useTemplateRef('load')
useIntersectionObserver(target, ([entry]) => {
  if (entry.isIntersecting && hasNextPage) {
    fetchNextPage()
  }
})

const notifications = computed(() => data?.value?.pages.flatMap((page) => page.notifications) ?? [])

const { mutate: markAllNotificationsAsReadMutation } = useMutation({
  mutationFn: markAllNotificationsAsRead,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  },
})

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
        <GeneralSettingsDialog v-model="isSettingsOpen" />
        <popover>
          <popover-trigger as="button" class="relative">
            <bell-icon
              :has-notifications="unreadNotificationsCount > 0"
              class="text-light-yellow"
              aria-label="Notifications"
              filled
            />
            <span
              v-if="unreadNotificationsCount > 0"
              class="absolute min-w-4 rounded-full bg-[#B10000] p-0.5 text-center font-mono text-xs leading-none font-bold"
              :class="{
                'top-1 right-[3px]': unreadNotificationsCount < 10,
                'top-1 right-px': unreadNotificationsCount >= 10,
              }"
              >{{ unreadNotificationsCount }}
            </span>
          </popover-trigger>
          <popover-content
            as="div"
            class="text-light-yellow relative mt-1 flex max-h-[calc(100vh-122px)] w-[436px] flex-col gap-4 overflow-x-hidden overflow-y-auto rounded-md border-none bg-[#252329] p-0 pb-4"
            align="end"
            style="scrollbar-gutter: stable"
          >
            <div
              class="sticky top-0 z-10 flex w-full items-center justify-between bg-[#252329] p-4 pe-1.5"
            >
              <h3 class="font-title text-xl font-bold">Notificações</h3>
              <div class="flex gap-2">
                <button
                  :disabled="data?.pages[0].meta.total_unread === 0"
                  class="flex items-center gap-2 rounded-md bg-white/10 p-1 px-3 transition-all hover:bg-white/12 active:bg-white/15"
                  @click="() => markAllNotificationsAsReadMutation()"
                  type="button"
                >
                  <check-icon />
                </button>
                <button
                  class="flex items-center gap-2 rounded-md bg-white/10 p-1 px-3 inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
                  :class="{
                    'inset-ring-accent': showReadNotifications,
                    'hover:inset-ring-accent/50 inset-ring-transparent': !showReadNotifications,
                  }"
                  @click="showReadNotifications = !showReadNotifications"
                  type="button"
                >
                  Mostrar lidas
                </button>
              </div>
            </div>
            <p
              v-if="notifications.length === 0"
              class="text-light-yellow/75 py-1 ps-4 pe-1.5 text-center text-sm"
            >
              Nenhuma notificação encontrada.
            </p>
            <ul v-else class="flex flex-col items-center gap-2 ps-4 pe-1.5">
              <transition-group name="notifications-list">
                <li v-for="notification in notifications" :key="notification.id">
                  <notification-item :notification="notification" />
                </li>
                <div class="py-3" v-if="hasNextPage" ref="load">
                  <LoadingSpinner />
                </div>
              </transition-group>
            </ul>
          </popover-content>
        </popover>
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
