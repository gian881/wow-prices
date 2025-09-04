<script setup lang="ts">
import tier1Image from '@/assets/tier-1.png'
import tier2Image from '@/assets/tier-2.png'
import tier3Image from '@/assets/tier-3.png'
import { computed } from 'vue'

const { quality, size } = defineProps<{
  name: string
  quality: number
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  image: string
  size: 'xxs' | 'xs' | 'sm' | 'md'
}>()

const tierImage = computed(() => {
  switch (quality) {
    case 1:
      return tier1Image
    case 2:
      return tier2Image
    case 3:
      return tier3Image
    default:
      return ''
  }
})

const tierImageClass = computed(() => {
  switch (quality) {
    case 1:
      if (size === 'xxs') return 'w-[10px] h-[10px] -left-[4px] -top-[4px]'
      if (size === 'xs') return 'w-[16px] h-[17px] -left-[7px] -top-[7px]'
      if (size === 'md') return 'w-[31px] h-[34px] -left-[13px] -top-[15px]'
      if (size === 'sm') return 'w-[25px] h-[27px] -left-[10px] -top-[12px]'

    case 2:
      if (size === 'xxs') return 'w-[14px] h-[10px] -left-[5px] -top-[5px]'
      if (size === 'xs') return 'w-[23px] h-[17px] -left-[8px] -top-[8px]'
      if (size === 'md') return 'w-[46px] h-[34px] -left-[14px] -top-[16px]'
      if (size === 'sm') return 'w-[37px] h-[27px] -left-[9px] -top-[13px]'
    case 3:
      if (size === 'xxs') return 'w-[12px] h-[11px] -left-[5px] -top-[5px]'
      if (size === 'xs') return 'w-[19px] h-[18px] -left-[7px] -top-[6px]'
      if (size === 'md') return 'w-[38px] h-[35px] -left-[13px] -top-[15px]'
      if (size === 'sm') return 'w-[30px] h-[28px] -left-[9px] -top-[12px]'
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
