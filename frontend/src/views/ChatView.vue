<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <!-- 消息列表 -->
    <div class="space-y-4 mb-8">
      <!-- 欢迎消息 -->
      <div v-if="messages.length === 0" class="text-center text-gray-400 py-16">
        <p class="text-lg">输入问题，开始问答</p>
        <p class="text-sm mt-2">基于你的知识库，AI 会检索相关内容并生成回答</p>
      </div>

      <!-- 消息 -->
      <div v-for="(msg, i) in messages" :key="i">
        <!-- 用户问题 -->
        <div class="flex justify-end mb-2">
          <div class="bg-blue-600 text-white rounded-2xl px-4 py-2 max-w-[80%]">
            {{ msg.question }}
          </div>
        </div>

        <!-- AI 回答 -->
        <div class="flex justify-start mb-2">
          <div class="bg-white border border-gray-200 rounded-2xl px-4 py-3 max-w-[85%]">
            <div class="prose prose-sm" v-html="formatAnswer(msg.answer)"></div>
            <div v-if="msg.sources?.length" class="mt-3 pt-2 border-t border-gray-100">
              <p class="text-xs text-gray-400">
                来源：{{ msg.sources.join(', ') }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="flex justify-start">
        <div class="bg-white border border-gray-200 rounded-2xl px-4 py-3">
          <div class="flex items-center gap-2 text-gray-400 text-sm">
            <div class="animate-pulse">正在检索和生成回答...</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3">
      <div class="max-w-3xl mx-auto flex gap-2">
        <input
          v-model="input"
          @keydown.enter="handleAsk"
          :disabled="loading"
          placeholder="输入你的问题..."
          class="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50"
        />
        <button
          @click="handleAsk"
          :disabled="loading || !input.trim()"
          class="bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { marked } from 'marked'
import { ask } from '../api.js'

// 配置 marked：关闭自动换行，保留原始 markdown
marked.setOptions({
  breaks: true,
  gfm: true,
})

const input = ref('')
const messages = ref([])
const loading = ref(false)

async function handleAsk() {
  const q = input.value.trim()
  if (!q || loading.value) return

  input.value = ''
  loading.value = true

  try {
    const res = await ask(q)
    messages.value.push({
      question: q,
      answer: res.answer,
      sources: res.sources,
    })
  } catch (e) {
    messages.value.push({
      question: q,
      answer: `出错了：${e.message}`,
      sources: [],
    })
  } finally {
    loading.value = false
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  }
}

function formatAnswer(text) {
  if (!text) return ''
  return marked.parse(text)
}
</script>
