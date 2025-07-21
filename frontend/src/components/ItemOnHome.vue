<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'

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

const rarityColors = {
  COMMON: 'border-common',
  UNCOMMON: 'border-uncommon',
  RARE: 'border-rare',
  EPIC: 'border-epic',
  LEGENDARY: 'border-legendary',
  ARTIFACT: 'border-artifact',
  TOKEN: 'border-token',
}
</script>
<template>
  <router-link
    :to="`/item/${id}`"
    class="flex max-w-[264px] gap-3 rounded p-2 transition-colors hover:bg-white/5"
  >
    <img :src="image" :alt="name" :class="`${rarityColors[rarity]} h-16 w-16 rounded border-2`" />
    <div class="flex flex-col items-start justify-between">
      <p class="overflow-hidden text-2xl font-semibold text-ellipsis whitespace-nowrap">
        {{ name }}
      </p>
      <div class="text-light-yellow flex items-center gap-1.5">
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
