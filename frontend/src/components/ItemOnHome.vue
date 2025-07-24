<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemImage from './ItemImage.vue'

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
}>()
</script>
<template>
  <router-link
    :to="`/item/${id}`"
    class="flex gap-3 rounded-lg p-2 transition-colors duration-500 hover:bg-white/5"
  >
    <item-image :name="name" :quality="quality" :rarity="rarity" :image="image" size="sm" />
    <div class="flex min-w-0 flex-col items-start justify-between">
      <p class="w-full overflow-hidden text-2xl font-semibold text-ellipsis whitespace-nowrap">
        {{ name }}
      </p>
      <div class="text-light-yellow flex items-center gap-1.5 font-medium">
        <div class="flex items-center gap-0.5">
          <p>{{ price.gold }}</p>
          <img :src="goldImage" alt="" class="h-4 w-4" />
        </div>
        <div class="flex items-center gap-0.5">
          <p>{{ price.silver }}</p>
          <img :src="silverImage" alt="" class="h-4 w-4" />
        </div>
      </div>
    </div>
  </router-link>
</template>
