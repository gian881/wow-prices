<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import CheckIcon from '@/components/icons/CheckIcon.vue'
import ItemImage from '@/components/item/ItemImage.vue'
import { markNotificationAsRead } from '@/services/api/endpoints/notification'
import type { Notification } from '@/types/notifications'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import { useTimeAgoIntl } from '@vueuse/core'
import { computed } from 'vue'

const props = defineProps<{
  notification: Notification
}>()

const title = computed(() => {
  switch (props.notification.type) {
    case 'price_above_alert':
      return 'Alerta de preço alto:'
    case 'price_below_alert':
      return 'Alerta de preço baixo:'
    case 'price_above_best_avg_alert':
      return 'Venda sugerida:'
    case 'price_below_best_avg_alert':
      return 'Compra sugerida:'
    default:
      return 'Notificação'
  }
})

const relativeTime = useTimeAgoIntl(new Date(props.notification.created_at), {
  locale: 'pt-BR',
})

const queryClient = useQueryClient()

const { mutate: markAsRead, isPending } = useMutation({
  mutationFn: async (id: number) => {
    try {
      await markNotificationAsRead(id)
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    } catch (error) {
      console.error('Failed to mark notification as read', error)
    }
  },
})
</script>

<template>
  <div
    class="flex items-start gap-2 rounded bg-white/5 p-2"
    :class="{ 'opacity-50': notification.read }"
  >
    <router-link :to="`/item/${notification.item.id}`" class="relative shrink-0">
      <img src="" alt="" aria-hidden="true" />
      <item-image
        :image="notification.item.image"
        :name="notification.item.name"
        :quality="notification.item.quality"
        :rarity="notification.item.rarity"
        size="xs"
      />
    </router-link>
    <div class="flex flex-col gap-0.5">
      <router-link :to="`/item/${notification.item.id}`" class="leading-tight font-semibold"
        >{{ title }} {{ props.notification.item.name }}</router-link
      >
      <div class="w-full text-xs">
        <p class="text-xs leading-normal">
          <span class="font-medium">{{ notification.item.name }}</span>
          está
          <span class="inline-flex items-center gap-0.5 font-semibold">
            <span>{{ notification.price_diff.gold }}</span
            ><img :src="goldImage" alt="g" class="h-3 w-3" />
            <span class="ml-1">{{ notification.price_diff.silver }}</span
            ><img :src="silverImage" alt="s" class="h-3 w-3" />
          </span>
          {{ notification.type.includes('above') ? 'acima' : 'abaixo' }}
          {{ notification.type.includes('best_avg') ? ' do "preço ideal"' : ' de' }}
          <span
            class="inline-flex items-center gap-0.5 font-semibold"
            v-if="notification.price_threshold"
          >
            <span>{{ notification.price_threshold.gold }}</span
            ><img :src="goldImage" alt="g" class="h-3 w-3" />
            <span class="ml-1">{{ notification.price_threshold.silver }}</span
            ><img :src="silverImage" alt="s" class="h-3 w-3" />
          </span>
          no momento.
        </p>
      </div>
      <div class="mt-1 flex items-center justify-between gap-2 text-xs">
        <div class="text-light-yellow flex items-center gap-1.5 font-semibold select-none">
          <div class="flex items-center gap-0.5">
            <p>{{ notification.current_price.gold }}</p>
            <img :src="goldImage" alt="" class="h-3 w-3" />
          </div>
          <div class="flex items-center gap-0.5">
            <p>{{ notification.current_price.silver }}</p>
            <img :src="silverImage" alt="" class="h-3 w-3" />
          </div>
        </div>
        <p class="text-light-yellow-200">{{ relativeTime }}</p>
      </div>
    </div>
    <div class="flex flex-col gap-2">
      <button
        class="ring-accent my-auto rounded-md bg-white/5 p-1.5 ring transition-colors hover:bg-white/8 active:bg-white/12"
        @click="() => markAsRead(notification.id)"
        :disabled="isPending"
        v-if="!notification.read"
      >
        <check-icon />
      </button>
    </div>
  </div>
</template>
