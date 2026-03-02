<template>
  <div class="home">
    <el-card class="card">
      <template #header>服务状态</template>
      <div v-if="health" class="health">
        <el-tag type="success" v-if="health.status === 'ok'">运行中</el-tag>
        <el-tag type="danger" v-else>异常</el-tag>
        <span class="version">版本 {{ health.version || '-' }}</span>
      </div>
      <div v-else-if="healthError" class="error">{{ healthError }}</div>
      <el-button v-else loading>检测中...</el-button>
    </el-card>
    <el-card class="card">
      <template #header>快捷入口</template>
      <div class="links">
        <el-link type="primary" href="#/daily-report">日报</el-link>
        <span class="sep">·</span>
        <el-link type="primary" href="#/news-trade">新闻→交易</el-link>
        <span class="sep">·</span>
        <el-link type="primary" href="#/chart">图表</el-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHealth, getErrorMessage } from '../api'

const health = ref(null)
const healthError = ref('')

onMounted(async () => {
  try {
    const { data } = await getHealth()
    health.value = data
  } catch (e) {
    healthError.value = getErrorMessage(e)
  }
})
</script>

<style scoped>
.home { display: flex; flex-direction: column; gap: 16px; }
.card { max-width: 480px; }
.health { display: flex; align-items: center; gap: 12px; }
.version { color: var(--el-text-color-secondary); font-size: 14px; }
.error { color: var(--el-color-danger); font-size: 14px; }
.links { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.sep { color: var(--el-text-color-placeholder); }
</style>
