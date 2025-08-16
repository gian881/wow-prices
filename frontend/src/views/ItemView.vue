<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import NotifyDownIcon from '@/components/icons/NotifyDownIcon.vue'
import NotifyUpIcon from '@/components/icons/NotifyUpIcon.vue'
import SettingsIcon from '@/components/icons/SettingsIcon.vue'
import ItemImage from '@/components/ItemImage.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { customBuyColorScale, customSellColorScale, getRelativeTime } from '@/utils'
import Plotly from 'plotly.js-dist-min'
import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const item = ref<{
  id: number
  name: string
  quality: number
  rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  image: string
  intent: 'sell' | 'buy' | 'both'
  quantity_threshold: number
  notify_sell: boolean
  notify_buy: boolean
  above_alert: {
    gold: number
    silver: number
  }
  below_alert: {
    gold: number
    silver: number
  }
  current_quantity: number
  current_price: {
    gold: number
    silver: number
  }
  average_price_data: {
    x: string[]
    y: string[]
    z: number[][]
  }
  average_quantity_data: {
    x: string[]
    y: string[]
    z: number[][]
  }
  last_week_data: {
    price: {
      x: string[]
      y: number[]
    }
    quantity: {
      x: string[]
      y: number[]
    }
  }
  last_timestamp: string
  selling: {
    weekday: string
    hour: number
    price: {
      gold: number
      silver: number
    }
    price_diff: {
      sign: string
      gold: number
      silver: number
    }
  } | null
  buying: {
    weekday: string
    hour: number
    price: {
      gold: number
      silver: number
    }
    price_diff: {
      sign: string
      gold: number
      silver: number
    }
  } | null
} | null>()

const loading = ref(false)
const error = ref<string | null>(null)

const intentEditForm = ref<'sell' | 'buy' | 'both'>('sell')
const notifySellEditForm = ref(false)
const notifyBuyEditForm = ref(false)
const quantityThresholdEditForm = ref(100)
const aboveAlertEditForm = ref({
  gold: 0,
  silver: 0,
})
const belowAlertEditForm = ref({
  gold: 0,
  silver: 0,
})
const isSettingsDialogOpen = ref(false)

watch(
  () => route.params.id,
  (id) => fetchItem(id),
  { immediate: true },
)

watch(item, (newItem) => {
  if (newItem && newItem.average_price_data) {
    nextTick(() => {
      Plotly.purge('priceChartDiv')
      Plotly.purge('quantityChartDiv')
      Plotly.purge('lastWeekChartDiv')

      console.log(newItem.last_week_data)

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

async function fetchItem(id: string | string[]) {
  error.value = item.value = null
  loading.value = true

  try {
    const response = await fetch(`http://127.0.0.1:8000/items/${id}`)
    if (!response.ok) {
      throw new Error(`Erro ao buscar item: ${response.statusText}`)
    }
    const jsonResponse = await response.json()
    item.value = jsonResponse
    intentEditForm.value = jsonResponse.intent
    notifySellEditForm.value = jsonResponse.notify_sell
    notifyBuyEditForm.value = jsonResponse.notify_buy
    quantityThresholdEditForm.value = jsonResponse.quantity_threshold
    aboveAlertEditForm.value = jsonResponse.above_alert
    belowAlertEditForm.value = jsonResponse.below_alert
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
  if (item.value) {
    intentEditForm.value = item.value.intent
    notifySellEditForm.value = item.value.notify_sell
    notifyBuyEditForm.value = item.value.notify_buy
    quantityThresholdEditForm.value = item.value.quantity_threshold
    aboveAlertEditForm.value = item.value.above_alert
    belowAlertEditForm.value = item.value.below_alert
  }
  isSettingsDialogOpen.value = false
}

async function saveSettings() {
  if (!item.value) return

  if (intentEditForm.value === 'sell') {
    notifyBuyEditForm.value = false
  }
  if (intentEditForm.value === 'buy') {
    notifySellEditForm.value = false
  }

  const updatedItem = {
    intent: intentEditForm.value,
    notify_sell: notifySellEditForm.value,
    notify_buy: notifyBuyEditForm.value,
    quantity_threshold: quantityThresholdEditForm.value,
    above_alert: aboveAlertEditForm.value,
    below_alert: belowAlertEditForm.value,
  }

  try {
    const response = await fetch(`http://localhost:8000/items/${item.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updatedItem),
    })

    if (!response.ok) {
      throw new Error(`Erro ao salvar configurações: ${response.statusText}`)
    }

    isSettingsDialogOpen.value = false
    fetchItem(route.params.id)
  } catch (err) {
    if (err instanceof Error) {
      error.value = err.message
    } else {
      error.value = String(err)
    }
  }
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
      <Dialog v-model:open="isSettingsDialogOpen">
        <DialogTrigger as-child>
          <button
            class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow rounded-md p-2.5 transition-colors"
            @click="isSettingsDialogOpen = true"
          >
            <settings-icon />
          </button>
        </DialogTrigger>
        <DialogContent
          class="text-light-yellow bg-midnight-light-200 px-6 py-4 md:max-w-[540px]"
          as-child
        >
          <form @submit.prevent="saveSettings">
            <DialogHeader class="flex flex-row items-center justify-between">
              <DialogTitle>Configurações</DialogTitle>
              <DialogDescription class="sr-only">
                Make changes to your profile here. Click save when you're done.
              </DialogDescription>
              <div class="flex items-center gap-2">
                <item-image
                  :image="item.image"
                  :name="item.name"
                  :quality="item.quality"
                  :rarity="item.rarity"
                  size="xxs"
                />
                <p>{{ item.name }}</p>
              </div>
            </DialogHeader>
            <div class="flex flex-col gap-1">
              <label class="font-title text-lg leading-[1.2] font-bold" for="intent"
                >Intenção</label
              >
              <Select id="intent" placeholder="Intenção" name="intent" v-model="intentEditForm">
                <select-trigger
                  class="text-light-yellow w-full border-none bg-white/10 text-sm focus:border"
                >
                  <select-value placeholder="Selecione a intenção" />
                </select-trigger>
                <select-content class="bg-[#323134]">
                  <select-group>
                    <select-item value="sell">Vender</select-item>
                    <select-item value="buy">Comprar</select-item>
                    <select-item value="both">Ambos</select-item>
                  </select-group>
                </select-content>
              </Select>
            </div>
            <div class="flex gap-2 text-sm leading-none">
              <button
                v-if="intentEditForm === 'sell' || intentEditForm === 'both'"
                class="flex flex-1 items-center gap-2 rounded-md bg-white/10 p-1 inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
                :class="{
                  'inset-ring-accent': notifySellEditForm,
                  'hover:inset-ring-accent/50 inset-ring-transparent': !notifySellEditForm,
                }"
                @click="notifySellEditForm = !notifySellEditForm"
                type="button"
              >
                <notify-up-icon />Notificar acima da média
              </button>
              <button
                v-if="intentEditForm === 'buy' || intentEditForm === 'both'"
                class="flex flex-1 items-center gap-2 rounded-md bg-white/10 p-1 inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
                :class="{
                  'inset-ring-accent': notifyBuyEditForm,
                  'hover:inset-ring-accent/50 inset-ring-transparent': !notifyBuyEditForm,
                }"
                @click="notifyBuyEditForm = !notifyBuyEditForm"
                type="button"
              >
                <notify-down-icon />Notificar abaixo da média
              </button>
            </div>
            <div class="flex flex-col gap-1">
              <label class="font-title text-lg leading-[1.2] font-bold" for="quantityThreshold"
                >Quantidade mínima</label
              ><input
                type="number"
                id="quantityThreshold"
                v-model="quantityThresholdEditForm"
                class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 hover:ring-accent/50 rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
              />
            </div>
            <div class="flex items-center gap-4">
              <div class="flex flex-col gap-1">
                <label class="font-title text-lg leading-[1.2] font-bold" for="aboveAlertGold"
                  >Alerta acima de</label
                >
                <div class="flex gap-2">
                  <div class="flex items-center justify-start gap-1">
                    <input
                      type="number"
                      id="aboveAlertGold"
                      v-model="aboveAlertEditForm.gold"
                      class="hover:ring-accent/50 focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                      placeholder="000"
                    />
                    <img :src="goldImage" class="h-6 w-6" />
                  </div>
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      id="aboveAlertSilver"
                      v-model="aboveAlertEditForm.silver"
                      class="hover:ring-accent/50 focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                      placeholder="00"
                    />
                    <img :src="silverImage" class="h-6 w-6" />
                  </div>
                </div>
              </div>
              <div class="flex flex-col gap-1">
                <label class="font-title text-lg leading-[1.2] font-bold" for="belowAlertGold"
                  >Alerta abaixo de</label
                >
                <div class="flex items-center gap-2">
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      id="belowAlertGold"
                      v-model="belowAlertEditForm.gold"
                      class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 hover:ring-accent/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                      placeholder="000"
                    />
                    <img :src="goldImage" class="h-6 w-6" />
                  </div>
                  <div class="flex items-center gap-1">
                    <input
                      type="number"
                      id="belowAlertSilver"
                      v-model="belowAlertEditForm.silver"
                      class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 hover:ring-accent/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                      placeholder="00"
                    />
                    <img :src="silverImage" class="h-6 w-6" />
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter class="text-light-yellow flex gap-8">
              <button
                type="button"
                class="border-accent flex-1 rounded-md border bg-white/5 p-1.5 transition-colors hover:bg-white/12 active:bg-white/20"
                @click="closeDialog()"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow flex-1 rounded-md p-1.5 transition-colors"
              >
                Salvar
              </button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <p class="text-lg">
        Quantidade:
        <span class="font-semibold">{{ item.current_quantity.toLocaleString('pt-BR') }}</span>
      </p>
      <p class="text-light-yellow-200 text-sm">
        Dados atualizados
        <span class="font-semibold">{{ getRelativeTime(item.last_timestamp) }}</span>
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
