<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import ItemImage from '@/components/item/ItemImage.vue'
import ItemSettingsDialog from '@/components/item/ItemSettingsDialog.vue'
import { getItem, getItemPlotData } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import type { DetailedItem, ItemPlotData } from '@/types/item'
import { customBuyColorScale, customSellColorScale } from '@/utils'
import { useTimeAgoIntl } from '@vueuse/core'
// @ts-expect-error we have no types for this package
import Plotly from 'plotly.js-cartesian-dist-min'
import { nextTick, ref, watch, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const item = ref<DetailedItem | null>()

const loading = ref(false)
const error = ref<string | null>(null)

const isSettingsDialogOpen = ref(false)
const itemPlotData = ref<ItemPlotData>()

watch(
  () => route.params.id,
  (id) => {
    fetchItem(id)
    fetchItemPlotData(id)
  },
  { immediate: true },
)

let relativeTime: ComputedRef<string> | null = null

watch(itemPlotData, (newItem) => {
  if (newItem && newItem.average_price_data) {
    nextTick(async () => {
      Plotly.purge('priceChartDiv')
      Plotly.purge('quantityChartDiv')
      Plotly.purge('lastWeekChartDiv')
      Plotly.newPlot(
        'lastWeekChartDiv',
        [
          {
            ...newItem.last_week_data.price,
            hovertemplate: '%{x}<br>Preço: <b>%{y:.2f}</b><extra></extra>',
            type: 'scatter',
            name: 'Preço',
            line: { color: '#783F99' },
          },
          {
            ...newItem.last_week_data.quantity,
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
            ...newItem.average_price_data,
            type: 'heatmap',
            colorscale: item.value?.intent == 'sell' ? customSellColorScale : customBuyColorScale,
            texttemplate: '%{z:.2f}',
            text: newItem.average_price_data.z,
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
            ...newItem.average_quantity_data,
            type: 'heatmap',
            colorscale: customSellColorScale,
            texttemplate: '%{z:.2f}',
            text: newItem.average_quantity_data.z,
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

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      fetchItem(route.params.id)
    }
  },
  { deep: true },
)

async function fetchItemPlotData(id: string | string[]) {
  try {
    itemPlotData.value = await getItemPlotData(id)
  } catch (err) {
    console.error('Erro ao buscar dados para os gráficos:', err)
  }
}

async function fetchItem(id: string | string[]) {
  error.value = item.value = null
  loading.value = true

  try {
    const responseData = await getItem(id)
    item.value = responseData
    relativeTime = useTimeAgoIntl(new Date(responseData.last_timestamp), {
      locale: 'pt-BR',
    })

    const qualityString =
      responseData.quality === 'normal' ? '' : ` - ${responseData.quality.replace(/\D/g, '')}`
    document.title = `${responseData.name}${qualityString} - WOW Prices`
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

function closeDialog() {
  isSettingsDialogOpen.value = false
}

async function saveSettings() {
  isSettingsDialogOpen.value = false
  await fetchItem(route.params.id)
}
</script>

<template>
  <p v-if="loading">Carregando dados...</p>
  <p v-if="error">{{ error }}</p>
  <div class="mt-8 flex justify-between" v-if="item">
    <div class="flex items-center gap-6">
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
        <p v-if="item.selling && item.intent !== 'buy'" class="text-lg">
          Melhor dia de venda:
          <span class="font-semibold"> {{ item.selling.weekday }}</span>
          às
          <span class="font-semibold">{{ item.selling.hour.toString().padStart(2, '0') }}:00</span>
        </p>
        <p v-if="item.buying && item.intent !== 'sell'" class="text-lg">
          Melhor dia de compra:
          <span class="font-semibold"> {{ item.buying.weekday }}</span>
          às
          <span class="font-semibold">{{ item.buying.hour.toString().padStart(2, '0') }}:00</span>
        </p>
        <div class="text-light-yellow flex items-center gap-2">
          <div class="flex items-center gap-1.5 text-xl font-medium">
            <div class="flex items-center gap-0.5">
              <p>{{ item.current_price.gold }}</p>
              <img :src="goldImage" alt="" class="h-5 w-5" />
            </div>
            <div class="flex items-center gap-0.5">
              <p>{{ item.current_price.silver }}</p>
              <img :src="silverImage" alt="" class="h-5 w-5" />
            </div>
          </div>
          <div class="flex items-center gap-1.5" v-if="item.selling && item.intent !== 'buy'">
            <div class="flex items-center gap-0.5">
              <p>({{ item.selling.price_diff.gold }}</p>
              <img :src="goldImage" alt="" class="h-4 w-4" />
            </div>
            <div class="flex items-center gap-0.5">
              <p>{{ item.selling.price_diff.silver }}</p>
              <img :src="silverImage" alt="" class="h-4 w-4" />
            </div>
            <span
              class="font-semibold"
              :class="{
                'text-red-500': item?.selling.price_diff.sign === 'negative',
                'text-green-500': item?.selling.price_diff.sign === 'positive',
              }"
              >{{ item?.selling.price_diff.sign === 'negative' ? 'abaixo' : 'acima' }}</span
            >
            do preço "ideal")
          </div>
          <div class="flex items-center gap-1.5" v-if="item.buying && item.intent !== 'sell'">
            <div class="flex items-center gap-0.5">
              <p>({{ item.buying.price_diff.gold }}</p>
              <img :src="goldImage" alt="" class="h-4 w-4" />
            </div>
            <div class="flex items-center gap-0.5">
              <p>{{ item.buying.price_diff.silver }}</p>
              <img :src="silverImage" alt="" class="h-4 w-4" />
            </div>
            <span
              class="font-semibold"
              :class="{
                'text-red-500': item?.buying.price_diff.sign === 'positive',
                'text-green-500': item?.buying.price_diff.sign === 'negative',
              }"
              >{{ item?.buying.price_diff.sign === 'negative' ? 'abaixo' : 'acima' }}</span
            >
            do preço "ideal")
          </div>
        </div>
      </div>
    </div>
    <div class="flex flex-col items-end justify-between gap-1 text-right">
      <div class="flex items-center gap-2">
        <p v-if="!item.is_active" class="font-semibold text-red-600">Item desativado</p>
        <item-settings-dialog
          @close="closeDialog"
          @save-settings="saveSettings"
          v-model:open="isSettingsDialogOpen"
          :item="item"
        />
      </div>

      <p class="text-lg">
        Quantidade:
        <span class="font-semibold">{{ item.current_quantity.toLocaleString('pt-BR') }}</span>
      </p>
      <p class="text-light-yellow-200 text-sm">
        Dados atualizados
        <span class="font-semibold">{{ relativeTime }}</span>
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
