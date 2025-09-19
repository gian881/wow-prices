<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemImage from '@/components/ItemImage.vue'
import type { Notification } from '@/types'
import { useTimeAgoIntl } from '@vueuse/core'
import { computed, ref } from 'vue'
import CheckIcon from './icons/CheckIcon.vue'
import DownCheckIcon from './icons/DownCheckIcon.vue'

const props = defineProps<{
  notification: Notification
}>()

const emit = defineEmits<{
  (e: 'mark-as-read', id: number): void
  (e: 'mark-as-read-all-below', id: number): void
}>()

const title = computed(() => {
  switch (props.notification.type) {
    case 'price_above_alert':
      return `Alerta de preço alto: ${props.notification.item.name}`
    case 'price_below_alert':
      return `Alerta de preço baixo: ${props.notification.item.name}`
    case 'price_above_best_avg_alert':
      return `Venda sugerida: ${props.notification.item.name}`
    case 'price_below_best_avg_alert':
      return `Compra sugerida: ${props.notification.item.name}`
    default:
      return 'Notificação'
  }
})

const markAsReadLoading = ref(false)
const relativeTime = useTimeAgoIntl(new Date(props.notification.created_at), {
  locale: 'pt-BR',
})

async function markAsRead() {
  markAsReadLoading.value = true
  try {
    const response = await fetch(
      `${import.meta.env.VITE_BACKEND_BASE_URL}/notifications/${props.notification.id}/mark-read`,
      {
        method: 'POST',
      },
    )

    if (!response.ok) {
      throw new Error('Failed to mark notification as read')
    }

    emit('mark-as-read', props.notification.id)
  } catch (error) {
    console.error('Failed to mark notification as read:', error)
  } finally {
    markAsReadLoading.value = false
  }
}
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
      <router-link :to="`/item/${notification.item.id}`" class="leading-tight font-semibold">{{
        title
      }}</router-link>
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
    <div class="flex gap-2 flex-col">
      <button
        class="ring-accent my-auto rounded-md bg-white/5 p-1.5 ring transition-colors hover:bg-white/8 active:bg-white/12"
        @click="markAsRead"
        :disabled="markAsReadLoading"
        v-if="!notification.read"
      >
        <check-icon />
      </button>
      <button
        class="ring-accent my-auto rounded-md bg-white/5 p-1.5 ring transition-colors hover:bg-white/8 active:bg-white/12"
        @click="$emit('mark-as-read-all-below', notification.id)"
        :disabled="markAsReadLoading"
        v-if="!notification.read"
      >
        <down-check-icon />
      </button>
    </div>
  </div>
</template>
