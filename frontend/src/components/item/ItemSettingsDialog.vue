<script setup lang="ts">
import goldImage from '@/assets/gold.png'
import silverImage from '@/assets/silver.png'
import tier1MidnightImage from '@/assets/tier-1-midnight.png'
import tier1Image from '@/assets/tier-1.png'
import tier2MidnightImage from '@/assets/tier-2-midnight.png'
import tier2Image from '@/assets/tier-2.png'
import tier3Image from '@/assets/tier-3.png'
import tier4Image from '@/assets/tier-4.png'
import tier5Image from '@/assets/tier-5.png'
import NotifyDownIcon from '@/components/icons/NotifyDownIcon.vue'
import NotifyUpIcon from '@/components/icons/NotifyUpIcon.vue'
import SettingsIcon from '@/components/icons/SettingsIcon.vue'
import ItemImage from '@/components/item/ItemImage.vue'
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
import { editItem } from '@/services/api/endpoints/item'
import type { Intent, Quality } from '@/types'
import type { DetailedItem } from '@/types/item'
import { ref } from 'vue'

const isOpen = defineModel('isOpen', { type: Boolean, default: false })
const props = defineProps<{
  item: DetailedItem
}>()

const emit = defineEmits<{
  'save-settings': []
  close: []
}>()

const intentEditForm = ref<Intent>(props.item.intent)
const notifySellEditForm = ref(props.item.notify_sell)
const notifyBuyEditForm = ref(props.item.notify_buy)
const quantityThresholdEditForm = ref(props.item.quantity_threshold)
const aboveAlertEditForm = ref(props.item.above_alert)
const belowAlertEditForm = ref(props.item.below_alert)
const isActiveEditForm = ref(props.item.is_active)
const qualityEditForm = ref<Quality>(props.item.quality)

function onClose() {
  isOpen.value = false
  emit('close')
}

async function onSaveSettings() {
  if (!props.item) return

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
    is_active: isActiveEditForm.value,
    quality: qualityEditForm.value,
  }

  try {
    await editItem(props.item.id, updatedItem)
    isOpen.value = false
    emit('save-settings')
  } catch (err) {
    console.error('Erro ao salvar configurações:', err)
  }
}
</script>
<template>
  <Dialog v-model:open="isOpen">
    <DialogTrigger as-child>
      <button
        class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow rounded-md p-2.5 transition-colors"
        @click="isOpen = true"
      >
        <settings-icon />
      </button>
    </DialogTrigger>
    <DialogContent
      class="text-light-yellow bg-midnight-light-200 px-6 py-4 md:max-w-[540px]"
      as-child
    >
      <form @submit.prevent="onSaveSettings">
        <DialogHeader class="flex flex-row items-center justify-between">
          <DialogTitle>Configurações</DialogTitle>
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
          <label class="font-title text-lg leading-[1.2] font-bold" for="intent">Intenção</label>
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
        <div class="flex items-start gap-4">
          <div class="flex flex-1 flex-col gap-1">
            <div class="font-title text-lg leading-[1.2] font-bold" for="quantityThreshold">
              Ativo
            </div>
            <label for="isActive">
              <input
                type="checkbox"
                id="isActive"
                v-model="isActiveEditForm"
                class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 hover:ring-accent/50 rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none"
              />
              Está ativo
            </label>
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <label class="font-title text-lg leading-[1.2] font-bold" for="quality"
              >Qualidade</label
            >
            <Select id="quality" placeholder="Intenção" name="intent" v-model="qualityEditForm">
              <select-trigger
                class="text-light-yellow w-full border-none bg-white/10 text-sm focus:border"
              >
                <select-value placeholder="Selecione a qualidade do item" />
              </select-trigger>
              <select-content class="bg-[#323134]">
                <select-group>
                  <select-item value="normal">Normal</select-item>
                  <select-item value="tier_1">
                    <img :src="tier1Image" alt="Imagem do tier 1" class="size-4" />
                    Tier 1
                  </select-item>
                  <select-item value="tier_2">
                    <img :src="tier2Image" alt="Imagem do tier 2" class="size-4" />
                    Tier 2
                  </select-item>
                  <select-item value="tier_3">
                    <img :src="tier3Image" alt="Imagem do tier 3" class="size-4" />
                    Tier 3
                  </select-item>
                  <select-item value="tier_4">
                    <img :src="tier4Image" alt="Imagem do tier 4" class="size-4" />
                    Tier 4
                  </select-item>
                  <select-item value="tier_5">
                    <img :src="tier5Image" alt="Imagem do tier 5" class="size-4" />
                    Tier 5
                  </select-item>
                  <select-item value="tier_1_midnight">
                    <img
                      :src="tier1MidnightImage"
                      alt="Imagem do tier 1 de Midnight"
                      class="size-4"
                    />
                    Tier 1 (Midnight)
                  </select-item>
                  <select-item value="tier_2_midnight">
                    <img
                      :src="tier2MidnightImage"
                      alt="Imagem do tier 2 de Midnight"
                      class="size-4"
                    />
                    Tier 2 (Midnight)
                  </select-item>
                </select-group>
              </select-content>
            </Select>
          </div>
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

        <DialogFooter class="text-light-yellow flex gap-4">
          <button
            type="button"
            class="border-accent flex-1 rounded-md border bg-white/5 p-1.5 transition-colors hover:bg-white/12 active:bg-white/20"
            @click="onClose"
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
</template>
