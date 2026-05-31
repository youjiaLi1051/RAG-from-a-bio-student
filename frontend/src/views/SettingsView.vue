<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <h2 class="text-lg font-semibold mb-6">LLM 设置</h2>

    <!-- 状态提示 -->
    <div v-if="message" class="mb-4 p-3 rounded-lg text-sm" :class="messageType === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
      {{ message }}
    </div>

    <!-- 未配置提示 -->
    <div v-if="!configured && !loading" class="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
      <p class="font-medium mb-1">尚未配置 LLM</p>
      <p>请填写以下信息后保存，才能使用问答功能。</p>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">API URL</label>
        <input
          v-model="form.api_url"
          type="text"
          placeholder="例如：https://token-plan-cn.xiaomimimo.com/v1"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
        <input
          v-model="form.api_key"
          type="password"
          :placeholder="configured ? '已设置，留空则保持不变' : '输入你的 API Key'"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">模型名称</label>
        <input
          v-model="form.model"
          type="text"
          placeholder="例如：mimo-v2.5"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      <div class="flex gap-3 pt-2">
        <button
          @click="saveConfig"
          :disabled="saving"
          class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-300"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>

    <div class="mt-6 p-4 bg-gray-50 rounded-xl text-sm text-gray-500">
      <p class="font-medium text-gray-700 mb-1">说明</p>
      <ul class="list-disc list-inside space-y-1">
        <li>配置保存在服务器本地，不会上传到任何外部服务</li>
        <li>API Key 仅保存在服务器端，不会暴露给前端</li>
        <li>请勿将配置文件上传到公开仓库</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getLlmSettings, saveLlmSettings } from '../api.js'

const form = reactive({
  api_url: '',
  api_key: '',
  model: '',
})

const configured = ref(false)
const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageType = ref('success')

async function loadConfig() {
  loading.value = true
  try {
    const res = await getLlmSettings()
    form.api_url = res.api_url || ''
    form.model = res.model || ''
    configured.value = res.configured
  } catch (e) {
    showMessage('加载失败: ' + e.message, 'error')
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    const payload = {}
    if (form.api_url) payload.api_url = form.api_url
    if (form.api_key) payload.api_key = form.api_key
    if (form.model) payload.model = form.model

    if (Object.keys(payload).length === 0) {
      showMessage('请至少填写一项配置', 'error')
      return
    }

    const res = await saveLlmSettings(payload)
    configured.value = res.configured
    form.api_key = ''  // 清空输入框中的 key
    showMessage('设置已保存')
  } catch (e) {
    showMessage('保存失败: ' + e.message, 'error')
  } finally {
    saving.value = false
  }
}

function showMessage(msg, type = 'success') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

onMounted(loadConfig)
</script>
