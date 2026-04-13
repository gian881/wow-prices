<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemOnCalculator from '@/components/item/ItemOnCalculator.vue'
import { getItems } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import type { Item } from '@/types/item'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, watch } from 'vue'

export type CalculatorItem = Item & {
  quantity: number
}

const queryClient = useQueryClient()

const { data: items } = useQuery({
  queryKey: ['calculatorItems'],
  queryFn: async () => {
    const returnedItems = await getItems({ intent: 'sell' })
    const savedItems = localStorage.getItem('items')

    if (!savedItems) {
      return returnedItems.map((item) => ({
        ...item,
        quantity: 0,
      }))
    }

    const parsedItems = JSON.parse(savedItems) as { id: number; quantity: number }[]

    const calculatorItems: CalculatorItem[] = returnedItems.map((item) => {
      const savedItem = parsedItems.find((saved) => saved.id === item.id)
      if (savedItem) {
        return {
          ...item,
          quantity: savedItem.quantity,
        }
      }
      return {
        ...item,
        quantity: 0,
      }
    })

    return calculatorItems
  },
  staleTime: 1000 * 60 * 60,
})

const totalPrice = computed<{
  gold: number
  silver: number
}>(() => {
  if (!items.value) {
    return { gold: 0, silver: 0 }
  }
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
  if (!items.value) return
  localStorage.setItem(
    'items',
    JSON.stringify(
      items.value.map((item) => ({
        id: item.id,
        quantity: item.quantity,
      })),
    ),
  )
}

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      queryClient.invalidateQueries({ queryKey: ['calculatorItems'] })
    }
  },
  { deep: true },
)
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
            queryClient.setQueryData(['calculatorItems'], (oldData: CalculatorItem[]) => {
              if (!oldData) return oldData
              return oldData.map((d) => {
                if (d.id === item.id) {
                  return { ...d, quantity: parseInt(quantity, 10) ? parseInt(quantity, 10) : 0 }
                }
                return d
              })
            })
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
