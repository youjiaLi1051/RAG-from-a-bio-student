<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <h2 class="text-lg font-semibold mb-6">统计信息</h2>

    <div class="grid grid-cols-2 gap-4">
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <p class="text-sm text-gray-500">文档数量</p>
        <p class="text-3xl font-bold text-blue-600 mt-1">{{ stats.document_count }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-5">
        <p class="text-sm text-gray-500">Chunk 数量</p>
        <p class="text-3xl font-bold text-green-600 mt-1">{{ stats.chunk_count }}</p>
      </div>
      <div class="bg-white rounded-xl border border-gray-200 p-5 col-span-2">
        <p class="text-sm text-gray-500">索引状态</p>
        <p class="text-lg font-medium mt-1">
          {{ stats.index_exists ? '✅ 已构建' : '❌ 未构建' }}
        </p>
      </div>
    </div>

    <div class="mt-8 text-sm text-gray-400">
      <p>更多信息（问答历史、知识点、复习统计）将在后续版本中添加。</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getStats } from '../api.js'

const stats = ref({
  document_count: 0,
  chunk_count: 0,
  index_exists: false,
})

onMounted(async () => {
  try {
    stats.value = await getStats()
  } catch (e) {
    console.error('Failed to load stats:', e)
  }
})
</script>
