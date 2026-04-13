<script setup lang="ts">
import ItemOnHome from '@/components/item/ItemOnHome.vue'
import { getTodayItems } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import { isNotificationOn, toggleNotification } from '@/utils'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { watch } from 'vue'

const queryClient = useQueryClient()

const {
  data: todayItems,
  isLoading: isTodayItemsLoading,
  isError,
  error: todayItemsError,
} = useQuery({
  queryKey: ['todayItems'],
  queryFn: getTodayItems,
  staleTime: 1000 * 60 * 5, // 5 minutos
})

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      queryClient.invalidateQueries({ queryKey: ['todayItems'] })
    }
  },
  { deep: true },
)
</script>

<template>
  <main class="mt-6">
    <h2 class="font-title text-3xl font-bold">Itens para vender hoje (preço médio)</h2>

    <div class="mt-4 text-center" v-if="isTodayItemsLoading">Carregando itens do dia...</div>
    <div class="mt-4 text-center" v-if="isError">
      Erro ao carregar itens do dia: {{ todayItemsError }}
    </div>
    <div class="mt-6 flex flex-col gap-8" v-if="!isTodayItemsLoading && !todayItemsError">
      <div
        v-for="hour in todayItems"
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
