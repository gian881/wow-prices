<script lang="ts" setup>
import { cn } from '@/lib/utils'
import { LoaderCircle } from 'lucide-vue-next'
import type { HTMLAttributes } from 'vue'

const props = defineProps<{ class?: HTMLAttributes['class'] }>()
</script>

<template><LoaderCircle :class="cn('animate-spin', props.class)" /></template>
