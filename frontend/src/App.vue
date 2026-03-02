<template>
  <el-container class="app">
      <el-header class="header">
        <span class="title">ai-for-stock 决策台</span>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="nav"
        >
          <el-menu-item index="/">首页</el-menu-item>
          <el-menu-item index="/daily-report">日报</el-menu-item>
          <el-menu-item index="/news-trade">新闻→交易</el-menu-item>
          <el-menu-item index="/chart">图表</el-menu-item>
        </el-menu>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const activeMenu = computed(() => route.path || '/')
</script>

<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, "PingFang SC", sans-serif; }
.app { min-height: 100vh; }
.header {
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}
.title { font-weight: 600; margin-right: 24px; white-space: nowrap; }
.nav { flex: 1; border: none; }
.main { padding: 20px; max-width: 1200px; margin: 0 auto; width: 100%; }
</style>
