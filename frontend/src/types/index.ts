export interface User {
  id: number
  email: string
  username: string
  full_name: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface ChatFile {
  name: string
  url: string
  type: 'image' | 'pdf' | 'text'
}

export interface ChatMessage {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at?: string
  timestamp?: string
  sources?: Source[]
  files?: ChatFile[]
  facility_data?: FacilityData
}

export interface ChatRequest {
  message: string
  conversation_id?: number
  latitude?: number
  longitude?: number
}

export interface ChatResponse {
  reply: string
  conversation_id: number
  disclaimer: string
  sources?: Source[]
  title?: string
  facility_data?: FacilityData
}

export interface Source {
  title: string
  content: string
  relevance_score: number
  url?: string
  source?: string
}

export interface Facility {
  name: string
  rating?: number
  review_count?: number
  address?: string
  maps_url: string
  source: string
  specialty?: string
  facility_type?: string
  latitude?: number
  longitude?: number
  distance_km?: number
  phone?: string
  opening_hours?: string
  emergency?: boolean
}

export interface FacilityData {
  specialty: string
  facility_types: string[]
  search_url: string
  facilities: Facility[]
  latitude?: number
  longitude?: number
  resolved_location?: boolean
}

export interface Conversation {
  id: number
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

export interface HealthResponse {
  status: string
  version: string
}

export interface IngestResponse {
  success: boolean
  message: string
  chunks_ingested: number
  total_chunks?: number
}

export type Theme = 'light' | 'dark' | 'system'
