<template>
  <div class="page">
    <el-card>
      <template #header>标的 K 线图</template>
      <div class="form">
        <el-input v-model="symbol" placeholder="A股代码，如 600519" style="width: 120px; margin-right: 8px;" />
        <el-input-number v-model="days" :min="5" :max="250" style="width: 100px; margin-right: 8px;" />
        <span class="label">天</span>
        <el-button type="primary" :loading="loading" @click="loadChart">生成图表</el-button>
      </div>
      <el-alert v-if="chartError" type="error" :title="chartError" show-icon style="margin-top: 12px;" />
      <div v-if="chartSrc" class="chart-wrap">
        <img :src="chartSrc" alt="K线图" class="chart-img" @error="onImgError" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { fetchChart, getErrorMessage } from '../api'

const symbol = ref('600519')
const days = ref(60)
const loading = ref(false)
const chartError = ref('')
const chartSrc = ref('')

function onImgError() {
  chartError.value = chartError.value || '图片加载失败'
}

async function loadChart() {
  const s = (symbol.value || '').trim()
  if (!s) {
    chartError.value = '请输入股票代码'
    return
  }
  chartError.value = ''
  if (chartSrc.value) {
    URL.revokeObjectURL(chartSrc.value)
    chartSrc.value = ''
  }
  loading.value = true
  try {
    const url = await fetchChart(s, days.value)
    chartSrc.value = url
  } catch (e) {
    chartError.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

onUnmounted(() => {
  if (chartSrc.value) URL.revokeObjectURL(chartSrc.value)
})
</script>

<style scoped>
.form { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.label { font-size: 14px; color: var(--el-text-color-regular); }
.chart-wrap { margin-top: 16px; }
.chart-img { max-width: 100%; height: auto; display: block; }
</style>
