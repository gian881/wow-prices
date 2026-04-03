<script lang="ts" setup>
import BellIcon from '@/components/icons/BellIcon.vue'
import CheckIcon from '@/components/icons/CheckIcon.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import NotificationItem from '@/components/notifications/NotificationItem.vue'
import Popover from '@/components/ui/popover/Popover.vue'
import PopoverContent from '@/components/ui/popover/PopoverContent.vue'
import PopoverTrigger from '@/components/ui/popover/PopoverTrigger.vue'
import { getNotifications, markAllNotificationsAsRead } from '@/services/api/endpoints/notification'
import { useInfiniteQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useIntersectionObserver } from '@vueuse/core'
import { computed, ref, useTemplateRef } from 'vue'

const unreadNotificationsCount = ref(0)
const showReadNotifications = ref(false)
const queryClient = useQueryClient()

const { data, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery({
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

const notifications = computed(() =>
  data.value ? data.value.pages.flatMap((page) => page.notifications) : [],
)

const loadRef = useTemplateRef('load')
useIntersectionObserver(loadRef, ([entry]) => {
  if (entry.isIntersecting && hasNextPage && !isFetchingNextPage.value) {
    fetchNextPage()
  }
})

const { mutate: markAllNotificationsAsReadMutation } = useMutation({
  mutationFn: markAllNotificationsAsRead,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['notifications'] })
  },
})
</script>

<template>
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
</template>
