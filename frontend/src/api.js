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

// ── LLM 配置 ─────────────────────────────────────────

const LLM_CONFIG_KEY = 'biograph_llm_config'

function getLlmConfig() {
  try {
    const raw = localStorage.getItem(LLM_CONFIG_KEY)
    if (raw) {
      const cfg = JSON.parse(raw)
      const llm_config = {}
      if (cfg.api_url) llm_config.api_url = cfg.api_url
      if (cfg.api_key) llm_config.api_key = cfg.api_key
      if (cfg.model) llm_config.model = cfg.model
      return Object.keys(llm_config).length > 0 ? llm_config : undefined
    }
  } catch {
    // ignore
  }
  return undefined
}

// ── 问答 ──────────────────────────────────────────

export function ask(question, top_k = 20, top_n = 3) {
  const body = { question, top_k, top_n }
  const llm_config = getLlmConfig()
  if (llm_config) {
    body.llm_config = llm_config
  }
  return request('/qa/ask', {
    method: 'POST',
    body: JSON.stringify(body),
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
