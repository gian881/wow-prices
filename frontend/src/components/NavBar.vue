<script setup lang="ts">
import wowLogo from '@/assets/wow-logo.png'

import { RouterLink } from 'vue-router'
import SearchIcon from './icons/SearchIcon.vue'
</script>

<template>
  <header class="flex items-center justify-between pt-8">
    <router-link to="/" class="flex items-center gap-4">
      <img :src="wowLogo" alt="World of Warcraft: Ghosts of K'aresh Logo" />
      <h1 class="font-title text-5xl font-bold">WOW Prices</h1>
    </router-link>
    <div class="flex items-center gap-2">
      <router-link
        to="/calculator"
        class="text-accent-white hover:text-accent-400 mr-3 text-lg transition-colors duration-400 ease-in-out"
      >
        Calculadora
      </router-link>
      <input
        type="text"
        placeholder="Pesquisar item..."
        class="bg-midnight-light-100 placeholder:text-light-yellow/75 text-light-yellow min-w-80 rounded-lg px-4 py-2"
        aria-label="Search for items"
      />
      <button class="bg-accent button-shadow rounded-lg p-2">
        <SearchIcon class="text-light-yellow" aria-label="Search for items" />
      </button>
    </div>
  </header>
</template>
