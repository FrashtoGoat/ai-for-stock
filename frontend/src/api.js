import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || ''

export const api = axios.create({
  baseURL,
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

// 统一从接口错误中取出可读文案（FastAPI 的 detail 可能是 string 或 array）
export function getErrorMessage(err) {
  if (!err) return '未知错误'
  if (typeof err === 'string') return err
  const res = err.response
  if (!res) return err.message || '网络错误或后端未启动'
  const d = res.data?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) {
    const msg = d.map((x) => x.msg || x.loc?.join('.')).filter(Boolean)
    return msg.join('；') || res.statusText
  }
  if (res.data?.error) return `${res.data.detail || '错误'}：${res.data.error}`
  return res.statusText || err.message || `HTTP ${res.status}`
}

api.interceptors.response.use(
  (r) => r,
  (err) => {
    console.error('[api]', err.config?.url, err.response?.status, getErrorMessage(err))
    return Promise.reject(err)
  }
)

// 健康
export function getHealth() {
  return api.get('/health')
}

// 日报
export function getDailyReport(symbols) {
  const params = symbols ? { symbols } : {}
  return api.get('/api/daily-report', { params })
}

export function getDailyReportAndPush(symbols) {
  const params = symbols ? { symbols } : {}
  return api.get('/api/daily-report/push', { params })
}

// 新闻→交易
export function getSuggestions() {
  return api.get('/api/news-trade/suggestions')
}

export function getSuggestionsMulti() {
  return api.get('/api/news-trade/suggestions-multi')
}

export function runNewsTrade(dryRun = true, multi = false) {
  return api.post('/api/news-trade/run', null, {
    params: { dry_run: dryRun, multi },
  })
}

// 图表：请求 PNG，成功返回 blob URL，失败抛错（便于展示后端错误）
export async function fetchChart(symbol, days = 60) {
  try {
    const res = await api.get('/api/chart', {
      params: { symbol, days },
      responseType: 'blob',
    })
    const ct = res.headers['content-type'] || ''
    if (ct.includes('application/json')) {
      const text = await res.data.text()
      let msg = '图表加载失败'
      try {
        const j = JSON.parse(text)
        if (j.error) msg = j.detail ? `${j.detail}: ${j.error}` : j.error
        else if (j.detail) msg = j.detail
      } catch (_) {}
      throw new Error(msg)
    }
    return URL.createObjectURL(res.data)
  } catch (err) {
    if (err.response?.data instanceof Blob && err.response.status >= 400) {
      try {
        const text = await err.response.data.text()
        const j = JSON.parse(text)
        const msg = j.detail && j.error ? `${j.detail}: ${j.error}` : j.detail || j.error || text
        throw new Error(msg)
      } catch (e) {
        if (e instanceof Error && e.message && e !== err) throw e
      }
    }
    throw err
  }
}

export function chartUrl(symbol, days = 60) {
  const base = baseURL || ''
  return `${base}/api/chart?symbol=${encodeURIComponent(symbol)}&days=${days}`
}
