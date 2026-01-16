<template>
  <div v-if="loading" class="overlay">
    <div class="box"><span class="loader"></span> {{ text }}</div>
  </div>
</template>
<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useLoadingStore } from '../stores/ui'
const store = useLoadingStore()
const { loading, text } = storeToRefs(store)
</script>
<style>
.overlay{ position:fixed; inset:0; background:rgba(15, 23, 42, 0.4); backdrop-filter: blur(2px); display:flex; align-items:center; justify-content:center; z-index:9999; }
.overlay .box{ background:var(--bg-card); padding:24px 32px; border-radius:var(--radius-md); box-shadow:var(--shadow-lg); display: flex; align-items: center; gap: 12px; font-weight: 500; color: var(--text-main); }
</style>