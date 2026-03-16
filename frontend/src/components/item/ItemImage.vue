<script setup lang="ts">
import tier1MidnightImage from '@/assets/tier-1-midnight.png'
import tier1Image from '@/assets/tier-1.png'
import tier2MidnightImage from '@/assets/tier-2-midnight.png'
import tier2Image from '@/assets/tier-2.png'
import tier3Image from '@/assets/tier-3.png'
import tier4Image from '@/assets/tier-4.png'
import tier5Image from '@/assets/tier-5.png'
import type { Quality } from '@/types'
import { computed } from 'vue'

const { quality, size } = defineProps<{
  name: string
  quality: Quality
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  image: string
  size: 'xxs' | 'xs' | 'sm' | 'md'
}>()

const tierImage = computed(() => {
  switch (quality) {
    case 'tier_1':
      return tier1Image
    case 'tier_2':
      return tier2Image
    case 'tier_3':
      return tier3Image
    case 'tier_4':
      return tier4Image
    case 'tier_5':
      return tier5Image
    case 'tier_1_midnight':
      return tier1MidnightImage
    case 'tier_2_midnight':
      return tier2MidnightImage
    default:
      return ''
  }
})

const tierImageClass = computed(() => {
  switch (quality) {
    case 'tier_1':
    case 'tier_3':
    case 'tier_4':
    case 'tier_5':
    case 'tier_1_midnight':
    case 'tier_2_midnight':
      if (size === 'xxs') return 'w-2.5 h-2.5 -left-1 -top-1'
      if (size === 'xs') return 'w-4 h-4 -left-1.5 -top-1.5'
      if (size === 'sm') return 'w-6 h-6 -left-2 -top-2'
      if (size === 'md') return 'w-8 h-8 -left-3 -top-3'

    case 'tier_2':
      if (size === 'xxs') return 'w-3 h-3 -left-1 -top-1.5'
      if (size === 'xs') return 'w-5 h-5 -left-1.5 -top-2.5'
      if (size === 'sm') return 'w-8 h-8 -left-2.5 -top-4'
      if (size === 'md') return 'w-10 h-10 -left-3 -top-[18px]'
    default:
      return ''
  }
})
</script>

<template>
  <div class="relative shrink-0">
    <img v-if="tierImage !== ''" :src="tierImage" class="absolute" :class="tierImageClass" />

    <img
      :src="image"
      :alt="name"
      class="rounded"
      :class="{
        'h-6 w-6': size === 'xxs',
        'h-10 w-10': size === 'xs',
        'h-16 w-16': size === 'sm',
        'h-20 w-20': size === 'md',
        'border-2': size === 'sm' || size === 'md',
        border: size === 'xxs' || size === 'xs',

        'border-common': rarity === 'COMMON',
        'border-uncommon': rarity === 'UNCOMMON',
        'border-rare': rarity === 'RARE',
        'border-epic': rarity === 'EPIC',
        'border-legendary': rarity === 'LEGENDARY',
        'border-artifact': rarity === 'ARTIFACT',
        'border-token': rarity === 'TOKEN',
      }"
    />
  </div>
</template>
