<script setup lang="ts">
import ItemOnHome from '@/components/ItemOnHome.vue'
import { onMounted, ref } from 'vue'

// const hoursAndItems = ref<
//   {
//     hour: string
//     items: {
//       id: number
//       name: string
//       price: {
//         gold: number
//         silver: number
//       }
//       quality: number
//       rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
//       image: string
//     }[]
//   }[]
// >([
//   {
//     hour: '00:00',
//     items: [
//       {
//         id: 2,
//         name: 'Item 1',
//         price: {
//           gold: 16,
//           silver: 67,
//         },
//         quality: 0,
//         rarity: 'LEGENDARY',
//         image: 'https://picsum.photos/200',
//       },
//     ],
//   },
// ])

const items = ref<
  {
    id: number
    name: string
    price: {
      gold: number
      silver: number
    }
    quality: number
    image: string
    rarity: 'COMMON' | 'UNCOMMON' | 'RARE' | 'EPIC' | 'LEGENDARY' | 'ARTIFACT' | 'TOKEN'
  }[]
>([])
const loading = ref(false)
const error = ref<string | null>(null)

async function fetchItems() {
  loading.value = true
  error.value = null

  try {
    const response = await fetch('http://localhost:8000/items/')

    if (!response.ok) {
      throw new Error(`Erro ao buscar itens: ${response.statusText}`)
    }
    items.value = await response.json()
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

onMounted(() => {
  fetchItems()
})
</script>

<template>
  <main class="mt-6">
    <!-- <h2 class="font-title text-3xl font-bold">Itens para vender hoje</h2> -->

    <!-- <div class="mt-6 flex flex-col gap-8">
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
          >
        </item-on-home>
        </div>
      </div>
    </div> -->
    <div>
      <h2 class="font-title text-3xl font-bold">Itens</h2>
      <div
        class="bg-midnight-light-200 mt-4 grid grid-cols-1 gap-4 rounded-lg p-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      >
        <item-on-home
          v-for="item in items"
          :key="item.id"
          :id="item.id"
          :name="item.name"
          :price="item.price"
          :quality="item.quality"
          :image="item.image"
          :rarity="item.rarity"
        >
        </item-on-home>
      </div>
    </div>
  </main>
</template>
