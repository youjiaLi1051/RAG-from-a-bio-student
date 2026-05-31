<template>
  <div class="max-w-3xl mx-auto px-4 py-8">
    <!-- 操作栏 -->
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-lg font-semibold">文档管理</h2>
      <div class="flex gap-2">
        <label class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors cursor-pointer">
          上传文档
          <input type="file" accept=".txt,.md,.docx,.pdf" @change="handleUpload" class="hidden" />
        </label>
        <button
          @click="handleBuildIndex"
          :disabled="indexing"
          class="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:bg-gray-300"
        >
          {{ indexing ? '构建中...' : '重建索引' }}
        </button>
      </div>
    </div>

    <!-- 状态提示 -->
    <div v-if="message" class="mb-4 p-3 rounded-lg text-sm" :class="messageType === 'error' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
      {{ message }}
    </div>

    <!-- 文档列表 -->
    <div v-if="documents.length === 0" class="text-center text-gray-400 py-12">
      暂无文档，请上传
    </div>

    <div v-else class="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
      <div v-for="doc in documents" :key="doc.name" class="flex items-center justify-between px-4 py-3">
        <div>
          <p class="text-sm font-medium">{{ doc.name }}</p>
          <p class="text-xs text-gray-400">{{ formatSize(doc.size) }}</p>
        </div>
        <button
          @click="handleDelete(doc.name)"
          class="text-red-500 hover:text-red-700 text-sm"
        >
          删除
        </button>
      </div>
    </div>

    <!-- 索引状态 -->
    <div class="mt-6 p-4 bg-gray-50 rounded-xl text-sm text-gray-600">
      <p>索引状态：{{ indexExists ? '✅ 已构建' : '❌ 未构建' }}</p>
      <p v-if="indexing" class="text-blue-600 mt-1">⏳ 正在构建索引...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listDocuments, uploadDocument, deleteDocument, buildIndex, indexStatus } from '../api.js'

const documents = ref([])
const message = ref('')
const messageType = ref('success')
const indexing = ref(false)
const indexExists = ref(false)

async function loadDocuments() {
  try {
    const res = await listDocuments()
    documents.value = res.documents
  } catch (e) {
    showMessage(e.message, 'error')
  }
}

async function loadIndexStatus() {
  try {
    const res = await indexStatus()
    indexExists.value = res.exists
    indexing.value = res.indexing
  } catch (e) {
    // ignore
  }
}

async function handleUpload(e) {
  const file = e.target.files[0]
  if (!file) return

  try {
    await uploadDocument(file)
    showMessage(`已上传: ${file.name}`)
    await loadDocuments()
  } catch (e) {
    showMessage(e.message, 'error')
  }

  e.target.value = ''
}

async function handleDelete(filename) {
  if (!confirm(`确定删除 ${filename}？`)) return

  try {
    await deleteDocument(filename)
    showMessage(`已删除: ${filename}`)
    await loadDocuments()
  } catch (e) {
    showMessage(e.message, 'error')
  }
}

async function handleBuildIndex() {
  try {
    await buildIndex()
    showMessage('索引构建已开始，请稍候...')
    indexing.value = true

    // 轮询状态
    const check = setInterval(async () => {
      await loadIndexStatus()
      if (!indexing.value) {
        clearInterval(check)
        showMessage('索引构建完成！')
      }
    }, 2000)
  } catch (e) {
    showMessage(e.message, 'error')
  }
}

function showMessage(msg, type = 'success') {
  message.value = msg
  messageType.value = type
  setTimeout(() => { message.value = '' }, 3000)
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

onMounted(() => {
  loadDocuments()
  loadIndexStatus()
})
</script>
