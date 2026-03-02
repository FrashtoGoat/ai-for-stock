<template>
  <div class="page">
    <el-card>
      <template #header>新闻→操作建议</template>
      <div class="actions">
        <el-button type="primary" :loading="suggestLoading" @click="fetchSuggestions">单视角建议</el-button>
        <el-button :loading="multiLoading" @click="fetchSuggestionsMulti">多视角建议</el-button>
      </div>
      <el-alert v-if="suggestError" type="error" :title="suggestError" show-icon style="margin-top: 12px;" />
      <div v-if="suggestResult" class="result">
        <h4>行业与标的</h4>
        <pre class="pre">{{ JSON.stringify(suggestResult.industries_and_symbols || {}, null, 2) }}</pre>
        <h4>建议</h4>
        <pre class="pre">{{ JSON.stringify(suggestResult.suggestions || {}, null, 2) }}</pre>
      </div>
    </el-card>
    <el-card>
      <template #header>执行链路（建议 + 可选下单）</template>
      <div class="actions">
        <el-button :loading="runLoading" @click="run(true, false)">仅建议（dry_run）</el-button>
        <el-button @click="run(true, true)">多视角仅建议</el-button>
        <el-button type="warning" :loading="runLoading" @click="run(false, false)">模拟下单</el-button>
        <el-button type="warning" @click="run(false, true)">多视角+模拟下单</el-button>
      </div>
      <el-alert v-if="runError" type="error" :title="runError" show-icon style="margin-top: 12px;" />
      <div v-if="runResult" class="result">
        <pre class="pre">{{ JSON.stringify(runResult, null, 2) }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { getSuggestions, getSuggestionsMulti, runNewsTrade, getErrorMessage } from '../api'

const suggestLoading = ref(false)
const multiLoading = ref(false)
const suggestResult = ref(null)
const suggestError = ref('')
const runLoading = ref(false)
const runResult = ref(null)
const runError = ref('')

async function fetchSuggestions() {
  suggestError.value = ''
  suggestResult.value = null
  suggestLoading.value = true
  try {
    const { data } = await getSuggestions()
    suggestResult.value = data
  } catch (e) {
    suggestError.value = getErrorMessage(e)
  } finally {
    suggestLoading.value = false
  }
}

async function fetchSuggestionsMulti() {
  suggestError.value = ''
  suggestResult.value = null
  multiLoading.value = true
  try {
    const { data } = await getSuggestionsMulti()
    suggestResult.value = data
  } catch (e) {
    suggestError.value = getErrorMessage(e)
  } finally {
    multiLoading.value = false
  }
}

async function run(dryRun, multi) {
  runError.value = ''
  runResult.value = null
  runLoading.value = true
  try {
    const { data } = await runNewsTrade(dryRun, multi)
    runResult.value = data
  } catch (e) {
    runError.value = getErrorMessage(e)
  } finally {
    runLoading.value = false
  }
}
</script>

<style scoped>
.actions { display: flex; flex-wrap: wrap; gap: 8px; }
.result { margin-top: 16px; text-align: left; }
.result h4 { margin: 12px 0 6px; font-size: 14px; }
.pre { background: var(--el-fill-color-light); padding: 12px; border-radius: 4px; overflow: auto; font-size: 12px; margin: 0; }
.page { display: flex; flex-direction: column; gap: 16px; }
</style>
