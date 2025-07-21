<script setup lang="ts">
import ItemOnHome from '@/components/ItemOnHome.vue'
import { ref } from 'vue'

const hoursAndItems = ref<
  {
    hour: string
    items: {
      id: number
      name: string
      price: {
        gold: number
        silver: number
      }
      quality: number
      rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
      image: string
    }[]
  }[]
>([
  {
    hour: '00:00',
    items: [
      {
        id: 2,
        name: 'Item 1',
        price: {
          gold: 16,
          silver: 67,
        },
        quality: 0,
        rarity: 'LEGENDARY',
        image: 'https://picsum.photos/200',
      },
    ],
  },
])
</script>

<template>
  <main class="mt-6">
    <h2 class="font-title text-3xl font-bold">Itens para vender hoje</h2>

    <div class="mt-6 flex flex-col gap-8">
      <div
        v-for="hour in hoursAndItems"
        :key="hour.hour"
        class="bg-midnight-light-200 rounded-lg p-4 pb-6"
      >
        <h3 class="font-title text-2xl font-bold">{{ hour.hour }}</h3>
        <div>
          <item-on-home
            v-for="item in hour.items"
            :key="item.name"
            :id="item.id"
            :name="item.name"
            :price="item.price"
            :quality="item.quality"
            :image="item.image"
            :rarity="item.rarity"
          >
          </item-on-home>
        </div>
      </div>
    </div>
  </main>
</template>
