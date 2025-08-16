<script setup lang="ts">
import ItemOnHome from '@/components/ItemOnHome.vue'
import { onMounted, ref } from 'vue'

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
      image: string
      rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
    }[]
  }[]
>([])

const items = ref<
  {
    id: number
    name: string
    price: {
      gold: number
      silver: number
    }
    quality: number
    image: string
    rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  }[]
>([])

const isTodayItemsLoading = ref(false)
const todayItemsError = ref<string | null>(null)

const isAllItemsLoading = ref(false)
const allItemsError = ref<string | null>(null)

async function fetchItems() {
  isTodayItemsLoading.value = true
  todayItemsError.value = null

  try {
    const response = await fetch('http://localhost:8000/items?order_by=price&order=desc')

    if (!response.ok) {
      throw new Error(`Erro ao buscar itens: ${response.statusText}`)
    }
    items.value = await response.json()
  } catch (err) {
    if (err instanceof Error) {
      todayItemsError.value = err.message
    } else {
      todayItemsError.value = String(err)
    }
  } finally {
    isTodayItemsLoading.value = false
  }
}

async function fetchTodayItems() {
  isAllItemsLoading.value = true
  allItemsError.value = null

  try {
    const response = await fetch('http://localhost:8000/items/today')

    if (!response.ok) {
      throw new Error(`Erro ao buscar itens: ${response.statusText}`)
    }
    hoursAndItems.value = await response.json()
  } catch (err) {
    if (err instanceof Error) {
      allItemsError.value = err.message
    } else {
      allItemsError.value = String(err)
    }
  } finally {
    isAllItemsLoading.value = false
  }
}

const textButton = ref('Todos os itens')
const textTitle = ref('Itens para vender hoje (preço médio)')
const view = ref<'all-items' | 'today-items'>('today-items')

onMounted(() => {
  fetchItems()
  fetchTodayItems()
})
</script>

<template>
  <main class="mt-6">
    <div class="flex items-center justify-between">
      <h2 class="font-title text-3xl font-bold">{{ textTitle }}</h2>
      <div class="flex items-center gap-4">
        <router-link
          to="/week"
          class="bg-accent button-shadow text-light-yellow mt-4 rounded-lg p-2 transition-colors duration-500 hover:bg-[#7344a6]"
        >
          Ver semana
        </router-link>
        <button
          @click="
            () => {
              textButton = textButton === 'Todos os itens' ? 'Itens do dia' : 'Todos os itens'
              view = view === 'all-items' ? 'today-items' : 'all-items'
              textTitle = view === 'all-items' ? 'Itens' : 'Itens para vender hoje'
            }
          "
          class="bg-accent button-shadow text-light-yellow mt-4 rounded-lg p-2 transition-colors duration-500 hover:bg-[#7344a6]"
        >
          {{ textButton }}
        </button>
      </div>
    </div>

    <div class="mt-4 text-center" v-if="isTodayItemsLoading && view === 'today-items'">
      Carregando itens do dia...
    </div>
    <div class="mt-4 text-center" v-if="todayItemsError && view === 'today-items'">
      Erro ao carregar itens do dia: {{ todayItemsError }}
    </div>
    <div
      class="mt-6 flex flex-col gap-8"
      v-if="view === 'today-items' && !isTodayItemsLoading && !todayItemsError"
    >
      <div
        v-for="hour in hoursAndItems"
        :key="hour.hour"
        class="bg-midnight-light-200 rounded-lg p-4 pb-6"
      >
        <h3 class="font-title text-2xl font-bold">{{ hour.hour }}</h3>
        <div class="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          <item-on-home
            v-for="item in hour.items"
            :key="item.name"
            :id="item.id"
            :name="item.name"
            :price="item.price"
            :quality="item.quality"
            :image="item.image"
            :rarity="item.rarity"
          />
        </div>
      </div>
    </div>

    <div v-if="view === 'all-items' && isAllItemsLoading" class="mt-4 text-center">
      Carregando todos os itens...
    </div>
    <div v-if="view === 'all-items' && allItemsError" class="mt-4 text-center text-red-500">
      Erro ao carregar todos os itens: {{ allItemsError }}
    </div>
    <div v-if="view === 'all-items' && !isAllItemsLoading && !allItemsError" class="mt-4">
      <div
        class="bg-midnight-light-200 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      >
        <item-on-home
          v-for="item in items"
          :key="item.id"
          :id="item.id"
          :name="item.name"
          :price="item.price"
          :quality="item.quality"
          :image="item.image"
          :rarity="item.rarity"
        />
      </div>
    </div>
  </main>
</template>
