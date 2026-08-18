import axios from 'axios'
import type { AuthResponse, ChatResponse, Conversation, User, FacilityData } from '../types'

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (!envUrl) return '/api'
  const trimmed = envUrl.trim().replace(/\/+$/, '')
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`
}

const API_BASE_URL = getApiBaseUrl()

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const url = error.config?.url || ''
    const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register')
    if (error.response?.status === 401 && !isAuthEndpoint && sessionStorage.getItem('token')) {
      sessionStorage.removeItem('token')
      sessionStorage.removeItem('user')
      window.location.href = '/login'
    }
    if (error.response) {
      throw new Error(error.response.data?.detail || error.message)
    }
    if (error.request) {
      throw new Error('Network error. Please check your connection.')
    }
    throw error
  },
)

export async function register(email: string, username: string, password: string, full_name: string): Promise<AuthResponse> {
  return apiClient.post('/v1/auth/register', { email, username, password, full_name })
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return apiClient.post('/v1/auth/login', { email, password })
}

export async function googleLogin(credential: string): Promise<AuthResponse> {
  return apiClient.post('/v1/auth/google', { credential })
}

export async function getMe(): Promise<User> {
  return apiClient.get('/v1/auth/me')
}

export async function getConversations(): Promise<Conversation[]> {
  return apiClient.get('/v1/conversations')
}

export async function getConversation(id: number): Promise<any> {
  return apiClient.get(`/v1/conversations/${id}`)
}

export async function createConversation(): Promise<any> {
  return apiClient.post('/v1/conversations')
}

export async function renameConversation(id: number, title: string): Promise<any> {
  return apiClient.put(`/v1/conversations/${id}/title`, { title })
}

export async function deleteConversation(id: number): Promise<any> {
  return apiClient.delete(`/v1/conversations/${id}`)
}

export async function searchConversations(query: string): Promise<Conversation[]> {
  return apiClient.get(`/v1/conversations/search/${query}`)
}

export async function sendChatMessage(message: string, conversationId?: number, fileSources?: string[]): Promise<ChatResponse> {
  return apiClient.post('/v1/chat', { message, conversation_id: conversationId, file_sources: fileSources })
}

export async function resetConversation(conversationId: number): Promise<any> {
  return apiClient.post(`/v1/reset?conversation_id=${conversationId}`)
}

export async function getHealthStatus(): Promise<{ status: string; version: string }> {
  return apiClient.get('/v1/health')
}

export async function uploadFile(file: File, filename: string): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('title', filename)
  return apiClient.post('/v1/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export async function findFacilities(healthIssue: string, location: string): Promise<FacilityData & { formatted_markdown: string }> {
  return apiClient.post('/v1/find-facilities', { health_issue: healthIssue, location })
}

export default apiClient
