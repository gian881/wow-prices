<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import NotifyDownIcon from '@/components/icons/NotifyDownIcon.vue'
import NotifyUpIcon from '@/components/icons/NotifyUpIcon.vue'
import ItemImage from '@/components/item/ItemImage.vue'
import ItemOnHome from '@/components/item/ItemOnHome.vue'
import LoadingSpinner from '@/components/LoadingSpinner.vue'
import {
  Dialog,
  DialogContent,
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
import { createItem, getItems, lookupItem } from '@/services/api/endpoints/item'
import { state as websocketState } from '@/services/websocketService'
import { isNotificationOn, toggleNotification } from '@/utils'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'

const allItemsError = ref<string | null>(null)
const showInactive = ref(false)
const queryClient = useQueryClient()

const {
  data: items,
  isLoading,
  isError,
} = useQuery({
  queryKey: ['items', showInactive],
  queryFn: () =>
    getItems({
      order_by: 'price',
      order: 'desc',
      show_inactive: showInactive.value,
    }),
  staleTime: 1000 * 60 * 60,
})

const sellItems = computed(() => {
  if (!items.value) return []
  return items.value.filter((item) => item.intent === 'sell')
})
const buyItems = computed(() => {
  if (!items.value) return []
  return items.value.filter((item) => item.intent === 'buy')
})
const bothItems = computed(() => {
  if (!items.value) return []
  return items.value.filter((item) => item.intent === 'both')
})

const isAddItemDialogOpen = ref(false)
const id = ref('')
const intent = ref<'buy' | 'sell' | 'both'>('sell')
const notifySell = ref(false)
const notifyBuy = ref(false)
const quantityThreshold = ref(100)
const aboveAlert = ref({
  gold: 0,
  silver: 0,
})
const belowAlert = ref({
  gold: 0,
  silver: 0,
})

function closeDialog() {
  isAddItemDialogOpen.value = false

  id.value = ''
  intent.value = 'sell'
  notifySell.value = false
  notifyBuy.value = false
  quantityThreshold.value = 100
  aboveAlert.value = {
    gold: 0,
    silver: 0,
  }
  belowAlert.value = {
    gold: 0,
    silver: 0,
  }
}

const {
  data: itemToAdd,
  isLoading: isSearchingItem,
  isError: isSearchItemError,
  error: searchItemError,
  refetch,
} = useQuery({
  queryKey: ['lookupItem', id],
  queryFn: () => lookupItem(id.value),
  enabled: false,
  retry: false,
})

const { mutate: createItemMutation } = useMutation({
  mutationFn: createItem,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['items', showInactive.value] })
    queryClient.invalidateQueries({ queryKey: ['todayItems'] })
    queryClient.invalidateQueries({ queryKey: ['weekItems'] })

    closeDialog()
  },
})

function searchItem() {
  if (!id.value) return
  refetch()
}

watch(
  () => websocketState.lastMessage,
  (newMessage) => {
    if (!newMessage) return
    if ('action' in newMessage && newMessage.action === 'new_data') {
      queryClient.invalidateQueries({ queryKey: ['items', showInactive.value] })
    }
  },
  { deep: true },
)
</script>

<template>
  <main>
    <div>
      <div class="flex items-center justify-between">
        <h2 class="font-title text-3xl font-bold">Todos os itens</h2>
        <div class="flex gap-2">
          <button
            class="rounded-md bg-white/10 px-3 py-1 text-center inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
            :class="{
              'inset-ring-accent': showInactive,
              'hover:inset-ring-accent/50 inset-ring-transparent': !showInactive,
            }"
            @click="showInactive = !showInactive"
            type="button"
          >
            Mostrar inativos
          </button>

          <Dialog v-model:open="isAddItemDialogOpen">
            <DialogTrigger as-child>
              <button
                class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow rounded-md p-2.5 transition-colors"
                @click="isAddItemDialogOpen = true"
              >
                Adicionar item
              </button>
            </DialogTrigger>
            <DialogContent
              class="text-light-yellow bg-midnight-light-200 px-6 py-4 md:max-w-[540px]"
              as-child
            >
              <form
                @submit.prevent="
                  () => {
                    if (!itemToAdd) return
                    createItemMutation({
                      ...itemToAdd,
                      intent: intent,
                      notifySell: notifySell,
                      notifyBuy: notifyBuy,
                      quantityThreshold: quantityThreshold,
                      aboveAlert: aboveAlert,
                      belowAlert: belowAlert,
                    })
                  }
                "
              >
                <DialogHeader class="flex flex-row items-end justify-between">
                  <DialogTitle>Adicionar item</DialogTitle>
                </DialogHeader>

                <div class="flex flex-col gap-1">
                  <label for="id" class="font-title text-lg leading-[1.2] font-bold">Id</label>
                  <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <input
                        type="text"
                        id="id"
                        v-model="id"
                        placeholder="Digite o id do item"
                        class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 hover:ring-accent/50 max-w-[144px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                        @blur="() => searchItem()"
                      />
                    </div>
                    <div v-if="isSearchingItem" class="flex items-center gap-2">
                      <loading-spinner />
                    </div>
                    <div v-if="isSearchItemError" class="flex items-center gap-2">
                      {{ searchItemError }}
                    </div>
                    <div class="flex items-center gap-2" v-else-if="itemToAdd">
                      <item-image
                        :image="itemToAdd.image"
                        :name="itemToAdd.name"
                        :quality="itemToAdd.quality"
                        :rarity="itemToAdd.rarity"
                        size="xxs"
                      />
                      <p>{{ itemToAdd.name }}</p>
                    </div>
                  </div>
                </div>

                <div class="flex flex-col gap-1">
                  <label class="font-title text-lg leading-[1.2] font-bold" for="intent"
                    >Intenção</label
                  >
                  <Select id="intent" placeholder="Intenção" name="intent" v-model="intent">
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
                    v-if="intent === 'sell' || intent === 'both'"
                    class="flex flex-1 items-center gap-2 rounded-md bg-white/10 p-1 inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
                    :class="{
                      'inset-ring-accent': notifySell,
                      'hover:inset-ring-accent/50 inset-ring-transparent': !notifySell,
                    }"
                    @click="notifySell = !notifySell"
                    type="button"
                  >
                    <notify-up-icon />Notificar acima da média
                  </button>
                  <button
                    v-if="intent === 'buy' || intent === 'both'"
                    class="flex flex-1 items-center gap-2 rounded-md bg-white/10 p-1 inset-ring-2 transition-all hover:bg-white/12 active:bg-white/15"
                    :class="{
                      'inset-ring-accent': notifyBuy,
                      'hover:inset-ring-accent/50 inset-ring-transparent': !notifyBuy,
                    }"
                    @click="notifyBuy = !notifyBuy"
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
                    v-model="quantityThreshold"
                    class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 hover:ring-accent/50 rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
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
                          v-model="aboveAlert.gold"
                          class="hover:ring-accent/50 focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                          placeholder="000"
                        />
                        <img :src="goldImage" class="h-6 w-6" />
                      </div>
                      <div class="flex items-center gap-1">
                        <input
                          type="number"
                          id="aboveAlertSilver"
                          v-model="aboveAlert.silver"
                          class="hover:ring-accent/50 focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
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
                          v-model="belowAlert.gold"
                          class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 hover:ring-accent/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
                          placeholder="000"
                        />
                        <img :src="goldImage" class="h-6 w-6" />
                      </div>
                      <div class="flex items-center gap-1">
                        <input
                          type="number"
                          id="belowAlertSilver"
                          v-model="belowAlert.silver"
                          class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/50 hover:ring-accent/50 max-w-[87px] rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
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
                    :disabled="!itemToAdd"
                    type="submit"
                    class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow flex-1 rounded-md p-1.5 transition-colors disabled:bg-gray-500"
                  >
                    Adicionar
                  </button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div v-if="isLoading" class="mt-4 text-center">Carregando todos os itens...</div>
      <div v-if="isError" class="mt-4 text-center text-red-500">
        Erro ao carregar todos os itens: {{ allItemsError }}
      </div>
      <div v-if="!isLoading && !isError" class="mt-4">
        <div v-if="sellItems.length > 0" class="mb-4">
          <h3 class="font-title text-2xl font-bold">Itens para vender</h3>
          <div
            class="bg-midnight-light-200 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
          >
            <item-on-home
              v-for="item in sellItems"
              :key="item.id"
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
        <div v-if="buyItems.length > 0" class="mb-4">
          <h3 class="font-title text-2xl font-bold">Itens para comprar</h3>
          <div
            class="bg-midnight-light-200 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
          >
            <item-on-home
              v-for="item in buyItems"
              :key="item.id"
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
        <div v-if="bothItems.length > 0" class="mb-4">
          <h3 class="font-title text-2xl font-bold">Itens para vender e comprar</h3>
          <div
            class="bg-midnight-light-200 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
          >
            <item-on-home
              v-for="item in bothItems"
              :key="item.id"
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
    </div>
  </main>
</template>
