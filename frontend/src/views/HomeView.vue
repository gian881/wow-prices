<script setup lang="ts">
import ItemOnHome from '@/components/ItemOnHome.vue'
import type { Item } from '@/types'
import { isNotificationOn, toggleNotification } from '@/utils'
import { onMounted, ref } from 'vue'

const hoursAndItems = ref<
  {
    hour: string
    items: Item[]
  }[]
>([])

const isTodayItemsLoading = ref(false)
const todayItemsError = ref<string | null>(null)

async function fetchTodayItems() {
  isTodayItemsLoading.value = true
  todayItemsError.value = null

  try {
    const response = await fetch('http://localhost:8000/items/today')

    if (!response.ok) {
      throw new Error(`Erro ao buscar itens: ${response.statusText}`)
    }
    hoursAndItems.value = await response.json()
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

onMounted(() => {
  fetchTodayItems()
})
</script>

<template>
  <main class="mt-6">
    <h2 class="font-title text-3xl font-bold">Itens para vender hoje (preço médio)</h2>

    <div class="mt-4 text-center" v-if="isTodayItemsLoading">Carregando itens do dia...</div>
    <div class="mt-4 text-center" v-if="todayItemsError">
      Erro ao carregar itens do dia: {{ todayItemsError }}
    </div>
    <div class="mt-6 flex flex-col gap-8" v-if="!isTodayItemsLoading && !todayItemsError">
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
            :is-notification-on="isNotificationOn(item)"
            @toggle-notification="toggleNotification(item)"
            notification-toggle
          />
        </div>
      </div>
    </div>
  </main>
</template>
