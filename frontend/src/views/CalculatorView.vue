<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemOnCalculator from '@/components/ItemOnCalculator.vue'
import { state as websocketState } from '@/services/websocketService'
import { computed, onMounted, ref, watch } from 'vue'

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

function saveItemQuantities() {
  console.log('Saving item quantities:', items.value)
  console.log('Total price:', totalPrice.value)
  localStorage.setItem(
    'items',
    JSON.stringify(
      items.value.map((item) => ({
        id: item.id,
        quantity: item.quantity,
      })),
    ),
  )
  console.log('Item quantities saved to localStorage')
  const savedItems = localStorage.getItem('items')
  console.log('Saved items from localStorage:', savedItems)
}

function loadItemQuantities() {
  const savedItems = localStorage.getItem('items')
  if (savedItems) {
    const parsedItems = JSON.parse(savedItems) as { id: number; quantity: number }[]
    parsedItems.forEach((savedItem) => {
      const item = items.value.find((item) => item.id === savedItem.id)
      if (item) {
        item.quantity = savedItem.quantity
      } else {
        console.warn(`Item with id ${savedItem.id} not found in fetched items`)
      }
    })
  }
}

function resetQuantities() {
  items.value.forEach((item) => {
    item.quantity = 0
  })
  saveItemQuantities()
}

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      fetchItems()
    }
  },
  { deep: true },
)

onMounted(async () => {
  await fetchItems()
  loadItemQuantities()
})
</script>

<template>
  <main class="mt-6">
    <div class="flex items-center justify-between">
      <h1 class="font-title text-3xl font-bold">Calculadora de possível venda</h1>
      <button
        class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow rounded-md p-2.5 transition-colors duration-400"
        @click="resetQuantities"
      >
        Limpar valores
      </button>
    </div>
    <div class="bg-midnight-light-200 mt-6 grid grid-cols-4 gap-4 overflow-x-auto rounded-md p-4">
      <item-on-calculator
        v-for="item in items"
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
        @blur="saveItemQuantities"
      />
    </div>
    <div
      class="bg-midnight-light-100 ring-accent fixed right-4 bottom-2 flex flex-col items-end rounded-xl p-2 ring"
    >
      <div class="flex items-center gap-2 rounded-md p-2">
        <span class="text-lg font-bold">{{ totalPrice.gold.toLocaleString('pt-BR') }}</span>
        <img :src="goldImage" alt="Gold" class="h-6 w-6" />
        <span class="text-lg font-bold">{{ totalPrice.silver }}</span>
        <img :src="silverImage" alt="Silver" class="h-6 w-6" />
      </div>
    </div>
  </main>
</template>
