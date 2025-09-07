<script setup lang="ts">
import { websocketService } from '@/services/websocketService'
import { onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'
import NavBar from './components/NavBar.vue'

onMounted(() => {
  websocketService.connect()
})

onUnmounted(() => {
  websocketService.disconnect()
})
</script>

<template>
  <div class="container mx-auto">
    <NavBar />
    <RouterView />
  </div>
</template>
