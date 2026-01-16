<template>
  <div v-if="visible" class="toast">{{ message }}</div>
</template>
<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useToastStore } from '../stores/ui'
const store = useToastStore()
const { visible, message } = storeToRefs(store)
</script>