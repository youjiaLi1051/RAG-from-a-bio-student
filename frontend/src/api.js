/**
 * API 客户端
 * 封装所有后端接口调用
 */

const BASE = '/api/v1'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '请求失败')
  }
  return res.json()
}

// ── 问答 ──────────────────────────────────────────

export function ask(question, top_k = 20, top_n = 3) {
  return request('/qa/ask', {
    method: 'POST',
    body: JSON.stringify({ question, top_k, top_n }),
  })
}

// ── LLM 设置 ─────────────────────────────────────

export function getLlmSettings() {
  return request('/settings/llm')
}

export function saveLlmSettings({ api_url, api_key, model }) {
  return request('/settings/llm', {
    method: 'POST',
    body: JSON.stringify({ api_url, api_key, model }),
  })
}

// ── 文档 ──────────────────────────────────────────

export function listDocuments() {
  return request('/documents')
}

export async function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/documents/upload`, { method: 'POST', body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || '上传失败')
  }
  return res.json()
}

export function deleteDocument(filename) {
  return request(`/documents/${encodeURIComponent(filename)}`, { method: 'DELETE' })
}

// ── 索引 ──────────────────────────────────────────

export function buildIndex() {
  return request('/documents/index', { method: 'POST' })
}

export function indexStatus() {
  return request('/documents/index/status')
}

// ── 统计 ──────────────────────────────────────────

export function getStats() {
  return request('/stats')
}

// ── 聊天记录 ──────────────────────────────────────

export function getHistory(limit = 50) {
  return request(`/qa/history?limit=${limit}`)
}

export function clearHistory() {
  return request('/qa/history', { method: 'DELETE' })
}
