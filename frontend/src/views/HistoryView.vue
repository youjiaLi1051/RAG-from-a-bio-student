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

    <div v-else class="space-y-3">
      <div
        v-for="record in history"
        :key="record.id"
        class="bg-white rounded-xl border border-gray-200 p-4 cursor-pointer hover:border-gray-300 transition-colors"
        @click="toggleExpand(record.id)"
      >
        <!-- 问题 + 时间 -->
        <div class="flex items-center justify-between mb-2">
          <p class="text-sm font-medium text-gray-900 flex-1 truncate">{{ record.question }}</p>
          <span class="text-xs text-gray-400 ml-2 shrink-0">{{ formatTime(record.timestamp) }}</span>
        </div>

        <!-- 回答预览（折叠时） -->
        <div v-if="!expanded[record.id]" class="text-sm text-gray-500 line-clamp-2">
          {{ record.answer }}
        </div>

        <!-- 完整回答（展开时） -->
        <div v-else>
          <div class="text-sm text-gray-700 prose prose-sm mt-2" v-html="formatAnswer(record.answer)"></div>
          <div v-if="record.sources?.length" class="mt-2 pt-2 border-t border-gray-100">
            <p class="text-xs text-gray-400">
              来源：{{ record.sources.join(', ') }}
            </p>
          </div>
        </div>

        <!-- 展开/折叠提示 -->
        <div class="text-xs text-gray-400 mt-2 text-center">
          {{ expanded[record.id] ? '点击收起' : '点击展开' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { marked } from 'marked'
import { getHistory, clearHistory } from '../api.js'

marked.setOptions({ breaks: true, gfm: true })

const history = ref([])
const expanded = reactive({})

function toggleExpand(id) {
  expanded[id] = !expanded[id]
}

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
  return marked.parse(text)
}

onMounted(loadHistory)
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
