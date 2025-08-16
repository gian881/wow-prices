<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemImage from './ItemImage.vue'
import BellIcon from './icons/BellIcon.vue'

defineProps<{
  id: number
  name: string
  price: {
    gold: number
    silver: number
  }
  quality: number
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  image: string
  size?: 'sm' | 'md'
  isNotificationOn?: boolean
  notificationToggle?: boolean
}>()

defineEmits<{
  (event: 'toggle-notification'): void
}>()
</script>
<template>
  <div class="flex gap-3 rounded-lg p-2 transition-colors duration-500 hover:bg-white/5">
    <router-link :to="`/item/${id}`" class="shrink-0">
      <item-image
        :name="name"
        :quality="quality"
        :rarity="rarity"
        :image="image"
        :size="size === 'sm' ? 'xs' : 'md'"
      />
    </router-link>
    <div class="flex w-full min-w-0 flex-col items-start justify-between">
      <router-link
        :to="`/item/${id}`"
        class="w-full overflow-hidden font-semibold text-ellipsis whitespace-nowrap"
        :class="{
          'text-base': size === 'sm',
          'text-2xl': size !== 'sm',
        }"
      >
        {{ name }}
      </router-link>
      <div class="flex w-full items-baseline justify-between gap-2">
        <div
          class="text-light-yellow flex items-center gap-1.5"
          :class="{
            'text-sm': size === 'sm',
            'text-base': size === 'md',
          }"
        >
          <div class="flex items-center gap-0.5">
            <p>{{ price.gold }}</p>
            <img
              :src="goldImage"
              alt=""
              :class="{
                'h-3 w-3': size === 'sm',
                'h-4 w-4': size === 'md',
              }"
            />
          </div>
          <div class="flex items-center gap-0.5">
            <p>{{ price.silver }}</p>
            <img
              :src="silverImage"
              alt=""
              :class="{
                'h-3 w-3': size === 'sm',
                'h-4 w-4': size === 'md',
              }"
            />
          </div>
        </div>

        <button @click="$emit('toggle-notification')" v-if="notificationToggle">
          <bell-icon :filled="isNotificationOn" class="h-6 w-6" />
        </button>
      </div>
    </div>
  </div>
</template>
