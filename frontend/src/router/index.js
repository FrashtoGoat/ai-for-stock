import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: '首页' } },
  { path: '/daily-report', name: 'DailyReport', component: () => import('../views/DailyReport.vue'), meta: { title: '日报' } },
  { path: '/news-trade', name: 'NewsTrade', component: () => import('../views/NewsTrade.vue'), meta: { title: '新闻→交易' } },
  { path: '/chart', name: 'Chart', component: () => import('../views/Chart.vue'), meta: { title: '图表' } },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
