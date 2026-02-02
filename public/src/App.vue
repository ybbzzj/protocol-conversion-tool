<template>
  <div class="header">
    <div class="nav container">
      <router-link to="/">首页</router-link>
      <router-link to="/extract">提取</router-link>
      <router-link to="/config">字段配置</router-link>
      <router-link to="/knowledge">知识库</router-link>
      <router-link to="/help">帮助</router-link>
    </div>
  </div>
  <router-view />
  <!-- 全局反馈提示 -->
  <Toast />
  <LoadingOverlay />
</template>
<script setup lang="ts">
import Toast from './components/Toast.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
</script>