<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold">聊天记录</h2>
      <button
        v-if="history.length > 0"
        @click="handleClear"
        class="text-red-500 hover:text-red-700 text-sm"
      >
        清空记录
      </button>
    </div>

    <div v-if="history.length === 0" class="text-center text-gray-400 py-12">
      暂无聊天记录
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="record in history"
        :key="record.id"
        class="bg-white rounded-xl border border-gray-200 p-4"
      >
        <!-- 问题 -->
        <div class="flex items-start gap-3 mb-3">
          <div class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 text-sm font-medium shrink-0">
            Q
          </div>
          <div class="flex-1">
            <p class="text-sm font-medium text-gray-900">{{ record.question }}</p>
            <p class="text-xs text-gray-400 mt-1">{{ formatTime(record.timestamp) }}</p>
          </div>
        </div>

        <!-- 回答 -->
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-green-600 text-sm font-medium shrink-0">
            A
          </div>
          <div class="flex-1">
            <div class="text-sm text-gray-700 prose prose-sm" v-html="formatAnswer(record.answer)"></div>
            <div v-if="record.sources?.length" class="mt-2 pt-2 border-t border-gray-100">
              <p class="text-xs text-gray-400">
                来源：{{ record.sources.join(', ') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHistory, clearHistory } from '../api.js'

const history = ref([])

async function loadHistory() {
  try {
    const res = await getHistory()
    history.value = res.history
  } catch (e) {
    console.error('Failed to load history:', e)
  }
}

async function handleClear() {
  if (!confirm('确定清空所有聊天记录？')) return
  try {
    await clearHistory()
    history.value = []
  } catch (e) {
    alert('清空失败: ' + e.message)
  }
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatAnswer(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}

onMounted(loadHistory)
</script>
