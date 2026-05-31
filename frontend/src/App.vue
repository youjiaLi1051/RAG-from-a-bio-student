<template>
  <div class="min-h-screen flex flex-col">
    <!-- 顶部导航 -->
    <nav class="bg-white border-b border-gray-200 px-6 py-3">
      <div class="max-w-5xl mx-auto flex items-center justify-between">
        <h1 class="text-xl font-bold text-blue-600">biograph</h1>
        <div class="flex gap-6">
          <router-link
            v-for="item in navItems"
            :key="item.path"
            :to="item.path"
            class="text-sm font-medium transition-colors"
            :class="$route.path === item.path ? 'text-blue-600' : 'text-gray-500 hover:text-gray-700'"
          >
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </nav>

    <!-- 页面内容 -->
    <main class="flex-1">
      <router-view />
    </main>
  </div>
</template>

<script setup>
const navItems = [
  { path: '/chat', label: '问答' },
  { path: '/files', label: '文档' },
  { path: '/history', label: '记录' },
  { path: '/settings', label: '设置' },
]
</script>
