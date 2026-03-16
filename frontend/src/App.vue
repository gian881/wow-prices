<script setup lang="ts">
import NavBar from '@/components/NavBar.vue'
import { websocketService } from '@/services/websocketService'
import { onMounted, onUnmounted } from 'vue'
import { RouterView } from 'vue-router'

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
