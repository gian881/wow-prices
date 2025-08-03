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
  averagePriceData: {
    x: string[]
    y: string[]
    z: number[][]
  }
  averageQuantityData: {
    x: string[]
    y: string[]
    z: number[][]
  }
  lastWeekData: {
    price: {
      x: string[]
      y: number[]
    }
    quantity: {
      x: string[]
      y: number[]
    }
  }
  lastTimeStamp: string
  selling: {
    weekday: string
    hour: number
    price: {
      gold: number
      silver: number
    }
    priceDiff: {
      sign: string
      gold: number
      silver: number
    }
  }
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
      Plotly.purge('priceChartDiv')
      Plotly.purge('quantityChartDiv')
      Plotly.purge('lastWeekChartDiv')

      console.log(newItem.lastWeekData)

      Plotly.newPlot(
        'lastWeekChartDiv',
        [
          {
            ...newItem.lastWeekData.price,
            hovertemplate: '%{x}<br>Preço: <b>%{y:.2f}</b><extra></extra>',
            type: 'scatter',
            name: 'Preço',
            line: { color: '#783F99' },
          },
          {
            ...newItem.lastWeekData.quantity,
            hovertemplate: '%{x}<br>Quantidade: <b>%{y}</b><extra></extra>',
            type: 'scatter',
            name: 'Quantidade',
            yaxis: 'y2',
            line: { color: '#52B3A0' },
          },
        ],
        {
          title: { text: 'Histórico de preço e quantidade' },
          font: {
            color: 'white',
            family: 'Poppins, sans-serif',
            size: 16,
          },
          paper_bgcolor: 'transparent',
          plot_bgcolor: 'transparent',
          legend: {
            orientation: 'h',
            x: -0.03,
            y: 1.15,
          },

          yaxis: {
            gridcolor: '#333',
            title: { text: 'Preço' },
            color: '#783F99',
            tickfont: { family: 'Poppins, sans-serif', size: 14 },
          },

          yaxis2: {
            title: { text: 'Quantidade' },
            overlaying: 'y',
            side: 'right',
            color: '#52B3A0',
            gridcolor: '#333',
            tickfont: { family: 'Poppins, sans-serif', size: 14 },
          },

          xaxis: {
            title: { text: 'Data e Hora' },
            type: 'date',
            tickformat: '%a %d/%m às %H:%M',
            gridcolor: '#444',
            tickfont: { family: 'Poppins, sans-serif', size: 14 },
          },

          hovermode: 'x',
          hoverlabel: {
            font: { family: 'Poppins, sans-serif', size: 14 },
          },
        },
      )
      Plotly.newPlot(
        'priceChartDiv',
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

      Plotly.newPlot(
        'quantityChartDiv',
        [
          {
            ...newItem.averageQuantityData,
            type: 'heatmap',
            colorscale: customColorScale,
            texttemplate: '%{z:.2f}',
            text: newItem.averageQuantityData.z,
            textfont: { family: 'Poppins, sans-serif', size: 14 },
            xgap: 1.5,
            ygap: 1.5,
            hovertemplate: '<b>%{x}, %{y}</b><br>Quantidade: %{z:.2f}<extra></extra>',
          },
        ],
        {
          title: { text: 'Quantidade pelo dia da semana e hora' },
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
        <p>
          Melhor dia de venda:
          <span class="font-bold"> {{ item.selling.weekday }}</span>
        </p>
        <div class="text-light-yellow flex items-center gap-2">
          <div class="flex items-center gap-1.5 text-xl font-medium">
            <div class="flex items-center gap-0.5">
              <p>{{ item.currentPrice.gold }}</p>
              <img :src="goldImage" alt="" class="h-5 w-5" />
            </div>
            <div class="flex items-center gap-0.5">
              <p>{{ item.currentPrice.silver }}</p>
              <img :src="silverImage" alt="" class="h-5 w-5" />
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="flex items-center gap-0.5">
              <p>({{ item.selling.priceDiff.gold }}</p>
              <img :src="goldImage" alt="" class="h-4 w-4" />
            </div>
            <div class="flex items-center gap-0.5">
              <p>{{ item.selling.priceDiff.silver }}</p>
              <img :src="silverImage" alt="" class="h-4 w-4" />
            </div>
            <span
              :class="`font-semibold ${item?.selling.priceDiff.sign === 'negative' ? 'text-red-500' : 'text-green-500'}`"
              >{{ item?.selling.priceDiff.sign === 'negative' ? 'abaixo' : 'acima' }}</span
            >
            do preço "ideal")
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

  <h2 class="font-title mt-8 text-3xl font-bold">Histórico de preços</h2>

  <div class="bg-midnight-light-200 mt-2 rounded-lg p-2">
    <div id="lastWeekChartDiv" class="my-chart-div"></div>
  </div>

  <h2 class="font-title mt-8 text-3xl font-bold">Heatmap de preços</h2>
  <div class="bg-midnight-light-200 mt-2 rounded-lg p-2">
    <div id="priceChartDiv" class="my-chart-div"></div>
  </div>

  <h2 class="font-title mt-8 text-3xl font-bold">Heatmap de quantidade</h2>
  <div class="bg-midnight-light-200 mt-2 rounded-lg p-2">
    <div id="quantityChartDiv" class="my-chart-div"></div>
  </div>
</template>

<style scoped>
.my-chart-div :deep(.svg-container) {
  margin: auto;
}
</style>
