<template>
  <div class="page">
    <el-card>
      <template #header>每日决策日报</template>
      <div class="form">
        <el-input
          v-model="symbols"
          placeholder="A股代码逗号分隔，如 600519,000001（留空用后端默认）"
          clearable
          style="max-width: 420px; margin-right: 12px;"
        />
        <el-button type="primary" :loading="loading" @click="fetchReport">生成日报</el-button>
        <el-button :loading="pushLoading" @click="fetchAndPush">生成并推送</el-button>
      </div>
      <el-alert v-if="error" type="error" :title="error" show-icon style="margin-top: 12px;" />
      <div v-if="report" class="report">
        <h4>一句话结论</h4>
        <p>{{ report.summary }}</p>
        <h4>买卖点位</h4>
        <p><strong>关注/买入：</strong>{{ report.buy_sell_points?.buy?.join('；') || '-' }}</p>
        <p><strong>警惕/卖出：</strong>{{ report.buy_sell_points?.sell?.join('；') || '-' }}</p>
        <h4>检查清单</h4>
        <ul class="checklist">
          <li v-for="item in report.checklist" :key="item.dimension_id">
            {{ item.dimension }}：{{ item.remark }} <span class="hint">({{ item.hint }})</span>
          </li>
        </ul>
        <p class="meta">查询标的 {{ report.symbols_queried?.join(',') }} · {{ report.generated_at }}</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getDailyReport, getDailyReportAndPush, getErrorMessage } from '../api'

const symbols = ref('')
const loading = ref(false)
const pushLoading = ref(false)
const report = ref(null)
const error = ref('')

async function fetchReport() {
  error.value = ''
  report.value = null
  loading.value = true
  try {
    const { data } = await getDailyReport(symbols.value || undefined)
    report.value = data
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function fetchAndPush() {
  error.value = ''
  report.value = null
  pushLoading.value = true
  try {
    const { data } = await getDailyReportAndPush(symbols.value || undefined)
    report.value = data.report
    if (data.push?.feishu) ElMessage.info('飞书: ' + (data.push.feishu.message ?? data.push.feishu.ok ?? ''))
    if (data.push?.dingtalk) ElMessage.info('钉钉: ' + (data.push.dingtalk.message ?? data.push.dingtalk.ok ?? ''))
    if (data.push?.hint) ElMessage.warning(data.push.hint)
  } catch (e) {
    error.value = getErrorMessage(e)
  } finally {
    pushLoading.value = false
  }
}
</script>

<style scoped>
.form { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.report { margin-top: 20px; text-align: left; }
.report h4 { margin: 16px 0 8px; font-size: 14px; }
.report p { margin: 0 0 8px; font-size: 14px; }
.checklist { margin: 0; padding-left: 20px; }
.checklist li { margin: 4px 0; }
.hint { color: var(--el-text-color-secondary); font-size: 12px; }
.meta { color: var(--el-text-color-secondary); font-size: 12px; margin-top: 12px; }
</style>
