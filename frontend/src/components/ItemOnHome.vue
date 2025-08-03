<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemImage from './ItemImage.vue'
import { computed } from 'vue'

const props = defineProps<{
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
}>()

const sizeClasses = computed(() => {
  if (props.size === 'sm') {
    return {
      name: 'text-base',
      coinText: 'text-sm',
      coinSize: 'h-3 w-3',
      itemImageSize: 'xs',
    }
  }
  // Default to 'md' if not specified
  return {
    name: 'text-2xl',
    coinText: 'text-base',
    coinSize: 'h-4 w-4',
    itemImageSize: 'md',
  }
})
</script>
<template>
  <router-link
    :to="`/item/${id}`"
    class="flex gap-3 rounded-lg p-2 transition-colors duration-500 hover:bg-white/5"
  >
    <item-image
      :name="name"
      :quality="quality"
      :rarity="rarity"
      :image="image"
      :size="size === 'sm' ? 'xs' : 'md'"
    />
    <div class="flex min-w-0 flex-col items-start justify-between">
      <p
        :class="`w-full overflow-hidden ${sizeClasses.name} font-semibold text-ellipsis whitespace-nowrap`"
      >
        {{ name }}
      </p>
      <div :class="`text-light-yellow flex items-center gap-1.5 ${sizeClasses.coinText}`">
        <div class="flex items-center gap-0.5">
          <p>{{ price.gold }}</p>
          <img :src="goldImage" alt="" :class="sizeClasses.coinSize" />
        </div>
        <div class="flex items-center gap-0.5">
          <p>{{ price.silver }}</p>
          <img :src="silverImage" alt="" :class="sizeClasses.coinSize" />
        </div>
      </div>
    </div>
  </router-link>
</template>
