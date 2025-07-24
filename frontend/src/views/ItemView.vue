<script setup lang="ts">
import Plotly from 'plotly.js-dist-min'
import ItemImage from '@/components/ItemImage.vue'
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import { ref, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { customColorScale, getRelativeTime } from '@/utils'

const route = useRoute()
const item = ref<{
  name: string
  quality: number
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  image: string
  currentQuantity: number
  currentPrice: {
    gold: number
    silver: number
  }
  lastTimeStamp: string
  //eslint-disable-next-line @typescript-eslint/no-explicit-any
  averagePriceData: any
} | null>()

const loading = ref(false)
const error = ref<string | null>(null)

watch(
  () => route.params.id,
  (id) => fetchItem(id),
  { immediate: true },
)

watch(item, (newItem) => {
  if (newItem && newItem.averagePriceData) {
    nextTick(() => {
      Plotly.newPlot(
        'chartDiv',
        [
          {
            ...newItem.averagePriceData,
            type: 'heatmap',
            colorscale: customColorScale,
            texttemplate: '%{z:.2f}',
            text: newItem.averagePriceData.z,
            textfont: { family: 'Poppins, sans-serif', size: 14 },
            xgap: 1.5,
            ygap: 1.5,
            hovertemplate: '<b>%{x}, %{y}</b><br>Preço: %{z:.2f}<extra></extra>',
          },
        ],
        {
          title: { text: 'Preço pelo dia da semana e hora' },
          width: 1000,
          height: 950,
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          font: {
            color: 'white',
            family: 'Poppins, sans-serif',
            size: 16,
          },
          xaxis: {
            title: { text: 'Dia da Semana' },
            side: 'bottom',
            showgrid: false,
          },
          yaxis: {
            title: { text: 'Hora do dia' },
            autorange: 'reversed',
            showgrid: false,
          },
        },
        {
          responsive: true,
        },
      )
    })
  }
})

async function fetchItem(id: string | string[]) {
  error.value = item.value = null
  loading.value = true

  try {
    const response = await fetch(`http://127.0.0.1:8000/items/${id}`)
    if (!response.ok) {
      throw new Error(`Erro ao buscar item: ${response.statusText}`)
    }
    item.value = await response.json()
  } catch (err) {
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = String(err)
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <p v-if="loading">Carregando dados...</p>
  <p v-if="error">{{ error }}</p>
  <div class="mt-8 flex justify-between" v-if="item">
    <div class="flex gap-6">
      <item-image
        v-if="item"
        :name="item?.name"
        :quality="item?.quality"
        :rarity="item?.rarity"
        :image="item?.image"
        size="md"
      ></item-image>
      <div class="flex flex-col justify-between">
        <h1 class="text-3xl font-semibold">{{ item.name }}</h1>
        <div class="text-light-yellow flex items-center gap-1.5 text-xl font-medium">
          <div class="flex items-center gap-0.5">
            <p>{{ item.currentPrice.gold }}</p>
            <img :src="goldImage" alt="" class="h-5 w-5" />
          </div>
          <div class="flex items-center gap-0.5">
            <p>{{ item.currentPrice.silver }}</p>
            <img :src="silverImage" alt="" class="h-5 w-5" />
          </div>
        </div>
      </div>
    </div>
    <div class="flex flex-col justify-between text-right">
      <p class="text-lg">
        Quantidade:
        <span class="font-semibold">{{ item.currentQuantity.toLocaleString('pt-BR') }}</span>
      </p>
      <p class="text-light-yellow-200 text-sm">
        Dados atualizados
        <span class="font-semibold">{{ getRelativeTime(item.lastTimeStamp) }}</span>
      </p>
    </div>
  </div>

  <h2 class="font-title mt-8 text-3xl font-bold">Heatmap de preços</h2>
  <div id="chartDiv" class="my-chart-div"></div>
</template>

<style scoped>
.my-chart-div :deep(.svg-container) {
  margin: auto;
}
</style>
