<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <h2 class="text-lg font-semibold mb-6">LLM 设置</h2>

    <!-- 状态提示 -->
    <div v-if="message" class="mb-4 p-3 rounded-lg text-sm" :class="messageType === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
      {{ message }}
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">API URL</label>
        <input
          v-model="config.api_url"
          type="text"
          placeholder="https://token-plan-cn.xiaomimimo.com/v1"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
        <input
          v-model="config.api_key"
          type="password"
          placeholder="输入你的 API Key"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
        <input
          v-model="config.model"
          type="text"
          placeholder="mimo-v2.5"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div class="flex gap-3 pt-2">
        <button
          @click="saveConfig"
          class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
        >
          保存
        </button>
        <button
          @click="resetConfig"
          class="bg-gray-200 text-gray-600 px-5 py-2 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors"
        >
          恢复默认
        </button>
      </div>
    </div>

    <div class="mt-6 p-4 bg-gray-50 rounded-xl text-sm text-gray-500">
      <p class="font-medium text-gray-700 mb-1">说明</p>
      <ul class="list-disc list-inside space-y-1">
        <li>配置保存在浏览器本地（localStorage），不会上传到服务器</li>
        <li>如果留空，将使用服务器端的默认配置</li>
        <li>API Key 仅在发送请求时传递，不会持久化到服务器</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const STORAGE_KEY = 'biograph_llm_config'

const DEFAULTS = {
  api_url: '',
  api_key: '',
  model: '',
}

const config = reactive({ ...DEFAULTS })
const message = ref('')
const messageType = ref('success')

function loadConfig() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const saved = JSON.parse(raw)
      Object.assign(config, DEFAULTS, saved)
    }
  } catch {
    // ignore
  }
}

function saveConfig() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...config }))
    showMessage('设置已保存')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  }
}

function resetConfig() {
  Object.assign(config, DEFAULTS)
  localStorage.removeItem(STORAGE_KEY)
  showMessage('已恢复默认设置')
}

function showMessage(msg, type = 'success') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

onMounted(loadConfig)
</script>
