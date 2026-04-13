<script setup lang="ts">
import ItemOnHome from '@/components/item/ItemOnHome.vue'
import { getWeekItems } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import { getTodayWeekdayIndex } from '@/utils'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { watch } from 'vue'

const queryClient = useQueryClient()

const { data, isLoading, error, isError } = useQuery({
  queryKey: ['weekItems'],
  queryFn: getWeekItems,
  staleTime: 1000 * 60 * 60, // 1 hour
})

const daysOfWeek = [
  { normalizedName: 'domingo', displayName: 'Domingo' },
  { normalizedName: 'segunda', displayName: 'Segunda' },
  { normalizedName: 'terca', displayName: 'Terça' },
  { normalizedName: 'quarta', displayName: 'Quarta' },
  { normalizedName: 'quinta', displayName: 'Quinta' },
  { normalizedName: 'sexta', displayName: 'Sexta' },
  { normalizedName: 'sabado', displayName: 'Sábado' },
]

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      queryClient.invalidateQueries({ queryKey: ['weekItems'] })
    }
  },
  { deep: true },
)
</script>

<template>
  <main class="mt-6">
    <h1 class="font-title text-3xl font-bold">Semana</h1>
    <div v-if="isLoading">Carregando</div>
    <div v-if="isError">{{ error }}</div>
    <div v-if="data" class="bg-midnight-light-200 mt-6 rounded-lg p-2">
      <div class="grid w-full grid-cols-7 gap-4">
        <p
          v-for="(day, index) in daysOfWeek"
          :key="day.normalizedName"
          :class="`text-light-yellow rounded-lg p-2 text-center font-semibold ${getTodayWeekdayIndex() === index ? 'bg-accent' : 'bg-midnight-light-100'}`"
        >
          {{ day.displayName }}
        </p>
      </div>
      <div class="mt-4 grid w-full grid-cols-7 gap-4">
        <div class="flex flex-col gap-4" v-for="day in daysOfWeek" :key="day.normalizedName">
          <div
            v-for="hour in data.find((item) => item.weekday === day.normalizedName)?.hours"
            :key="hour.hour"
            class="bg-midnight-light-150 flex flex-col gap-1.5 rounded-lg px-1 py-2"
          >
            <h2 class="font-title text-center font-bold">{{ hour.hour }}</h2>
            <item-on-home
              v-for="item in hour.items"
              :key="item.id"
              :item="item"
              :id="item.id"
              :name="item.name"
              :price="item.price"
              :quality="item.quality"
              :rarity="item.rarity"
              :image="item.image"
              size="sm"
            />
          </div>
        </div>
      </div>
    </div>
  </main>
</template>
