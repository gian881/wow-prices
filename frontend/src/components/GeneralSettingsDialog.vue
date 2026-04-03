<script setup lang="ts">
import SettingsIcon from '@/components/icons/SettingsIcon.vue'
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
import { numberOfDaysToMonthOrDays, valueUnitToDays } from '@/lib/utils'
import { getAllSettings, updateSetting } from '@/services/api/endpoints/settings'
import type { Setting } from '@/types/settings'
import { onMounted, ref } from 'vue'

const isOpen = ref(false)
const defaultWindowSetting = ref({
  value: 0,
  unit: 'days' as 'days' | 'months',
  allPeriod: false,
})

const settings = ref<Setting[]>()
const isSaving = ref(false)

const value = ref('')
const unit = ref<'days' | 'months'>('days')
const allPeriod = ref(false)

async function loadSettings() {
  try {
    settings.value = await getAllSettings()
    const convertedSettings = numberOfDaysToMonthOrDays(
      settings.value.find((s) => s.key === 'best_price_window_days')?.value ?? '0',
    )
    if (convertedSettings.value === 0) {
      allPeriod.value = true
      defaultWindowSetting.value = {
        value: 0,
        unit: 'days',
        allPeriod: true,
      }
    } else {
      defaultWindowSetting.value = {
        value: convertedSettings.value,
        unit: convertedSettings.unit,
        allPeriod: false,
      }
      value.value = convertedSettings.value.toString()
      unit.value = convertedSettings.unit
    }
  } catch {
  } finally {
  }
}

async function onSaveSettings() {
  try {
    isSaving.value = true
    const updatedSetting = await updateSetting(
      'best_price_window_days',
      allPeriod.value ? 'all' : valueUnitToDays(value.value, unit.value),
    )
    const convertedSettings = numberOfDaysToMonthOrDays(updatedSetting.value)
    value.value = convertedSettings.value.toString()
    unit.value = convertedSettings.unit
    defaultWindowSetting.value = {
      value: convertedSettings.value,
      unit: convertedSettings.unit,
      allPeriod: allPeriod.value,
    }
  } catch {
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
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
      class="text-light-yellow bg-midnight-light-200 border-none p-4 sm:max-w-[620px]"
      as-child
    >
      <form @submit.prevent="onSaveSettings">
        <DialogHeader>
          <DialogTitle>Configurações gerais</DialogTitle>
        </DialogHeader>

        <div class="flex flex-col gap-1">
          <label class="font-title text-lg leading-[1.2] font-bold"
            >Intervalo de referência de preço</label
          >
          <p class="text-light-yellow/75 text-sm">
            Tempo a ser considerado ao calcular o melhor dia e hora de compra/venda
          </p>
          <div class="flex items-center justify-between">
            <div class="flex gap-1">
              <input
                type="number"
                id="number"
                placeholder="Número"
                v-model="value"
                :disabled="allPeriod"
                class="focus:ring-accent text-light-yellow placeholder:text-light-yellow/75 hover:ring-accent/50 w-20 rounded-md bg-white/10 px-2 py-1.5 text-sm ring-2 ring-transparent transition-shadow outline-none disabled:cursor-not-allowed"
              />
              <Select
                id="quality"
                placeholder="Intenção"
                name="intent"
                v-model="unit"
                :disabled="allPeriod"
              >
                <select-trigger
                  class="text-light-yellow w-28 border-none bg-white/10 text-sm focus:border"
                >
                  <select-value />
                </select-trigger>
                <select-content class="bg-[#323134]">
                  <select-group>
                    <select-item value="days"> dias(s) </select-item>
                    <select-item value="months"> mês(es) </select-item>
                  </select-group>
                </select-content>
              </Select>
            </div>
            <label for="allPeriod" class="flex gap-1">
              <input type="checkbox" id="allPeriod" v-model="allPeriod" />
              <span class="text-light-yellow/75 text-sm">Considerar todo o período disponível</span>
            </label>
          </div>
        </div>

        <DialogFooter class="text-light-yellow flex gap-4">
          <button
            type="button"
            class="border-accent flex-1 rounded-md border bg-white/5 p-1.5 transition-colors hover:bg-white/12 active:bg-white/20"
            @click="
              () => {
                isOpen = false
                value = defaultWindowSetting.value.toString()
                unit = defaultWindowSetting.unit
                allPeriod = defaultWindowSetting.allPeriod
              }
            "
          >
            Cancelar
          </button>
          <button
            type="submit"
            :disabled="isSaving"
            class="bg-accent/80 hover:bg-accent/90 active:bg-accent button-shadow flex-1 rounded-md p-1.5 transition-colors disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span v-if="isSaving"> Salvando... </span>
            <span v-else> Salvar </span>
          </button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
</template>
