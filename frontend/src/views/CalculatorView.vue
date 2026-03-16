<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemOnCalculator from '@/components/item/ItemOnCalculator.vue'
import { getItems } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import type { Item } from '@/types/item'
import { computed, onMounted, ref, watch } from 'vue'

export type CalculatorItem = Item & {
  quantity: number
}

const items = ref<CalculatorItem[]>([])

async function fetchItems() {
  try {
    const returnedItems = await getItems({ intent: 'sell' })
    items.value = returnedItems.map((item) => ({ ...item, quantity: 0 }))
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
    <h1 class="font-title text-3xl font-bold">Calculadora de possível venda</h1>
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
