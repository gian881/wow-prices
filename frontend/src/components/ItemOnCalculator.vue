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
  quantity: number
}>()

defineEmits<{
  (e: 'input', value: string): void
  (e: 'blur'): void
}>()
</script>
<template>
  <div
    class="flex w-full max-w-sm shrink-0 gap-3 rounded-lg p-2 transition-colors duration-500 hover:bg-white/5"
  >
    <item-image :name="name" :quality="quality" :rarity="rarity" :image="image" size="md" />
    <div class="flex w-full min-w-0 flex-col items-start justify-between">
      <p class="w-full overflow-hidden text-2xl font-semibold text-ellipsis whitespace-nowrap">
        {{ name }}
      </p>
      <div class="flex w-full items-center justify-between gap-2">
        <div class="text-light-yellow flex items-center gap-1.5 text-base">
          <div class="flex items-center gap-0.5">
            <p>{{ price.gold }}</p>
            <img :src="goldImage" alt="" class="h-4 w-4" />
          </div>
          <div class="flex items-center gap-0.5">
            <p>{{ price.silver }}</p>
            <img :src="silverImage" alt="" class="h-4 w-4" />
          </div>
        </div>
        <div class="flex items-center gap-2">
          <input
            type="text"
            :value="quantity"
            @input="$emit('input', ($event.target as HTMLInputElement)?.value)"
            @blur="$emit('blur')"
            class="w-12 rounded-md border border-gray-300 p-1"
          />
          <!-- <button class="button-shadow rounded-xs bg-red-600 p-0.5" @click="$emit('')"><x-icon /></button> -->
        </div>
      </div>
    </div>
  </div>
</template>
