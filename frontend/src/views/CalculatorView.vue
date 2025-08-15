<script setup lang="ts">
import ItemOnCalculator from '@/components/ItemOnCalculator.vue'
import { computed, onMounted, ref } from 'vue'

export type Item = {
  id: number
  name: string
  price: {
    gold: number
    silver: number
  }
  quality: number
  image: string
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  quantity: number
}

const items = ref<Item[]>([])
const searchTerm = ref('')

async function fetchItems() {
  try {
    const response = await fetch('http://localhost:8000/items?intent=sell')
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
    items.value = await response.json()
    items.value.forEach((item) => {
      item.quantity = 0
    })
  } catch (error) {
    console.error('Error fetching items:', error)
  }
}

const totalPrice = computed<{
  gold: number
  silver: number
}>(() => {
  return items.value.reduce(
    (acc, item) => {
      acc.gold +=
        item.price.gold * item.quantity + Math.floor((item.price.silver * item.quantity) / 100)
      acc.silver = (acc.silver + item.price.silver * item.quantity) % 100
      return acc
    },
    { gold: 0, silver: 0 },
  )
})

onMounted(() => {
  fetchItems()
})
</script>

<template>
  <pre>{{ totalPrice }}</pre>
  <h1 class="font-title text-3xl font-bold">Calculadora de possível venda</h1>
  <input type="text" v-model="searchTerm" />
  <div class="bg-midnight-light-200 mt-4 grid grid-cols-4 gap-4 overflow-x-auto rounded-md p-4">
    <item-on-calculator
      v-for="item in items.filter((item) =>
        item.name.toLowerCase().includes(searchTerm.toLowerCase()),
      )"
      :key="item.id"
      :id="item.id"
      :name="item.name"
      :price="item.price"
      :quality="item.quality"
      :image="item.image"
      :rarity="item.rarity"
      :quantity="item.quantity"
      @input="
        (quantity) => {
          item.quantity = parseInt(quantity, 10) ? parseInt(quantity, 10) : 0
        }
      "
    />
  </div>
</template>
