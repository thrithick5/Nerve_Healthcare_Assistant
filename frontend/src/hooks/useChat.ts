import { useState, useCallback, useRef } from 'react'
import type { ChatMessage, ChatResponse } from '../types'
import { sendChatMessage, resetConversation as apiResetConversation, getBrowserLocation } from '../services/api'

interface UseChatReturn {
  messages: ChatMessage[]
  isLoading: boolean
  conversationId: number | null
  sendMessage: (message: string) => Promise<void>
  resetConversation: () => Promise<void>
  clearMessages: () => void
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<number | null>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      let latitude: number | undefined
      let longitude: number | undefined
      try {
        const coords = await getBrowserLocation()
        if (coords) {
          latitude = coords.latitude
          longitude = coords.longitude
        }
      } catch {
        // geolocation is optional — continue without it
      }

      const response: ChatResponse = await sendChatMessage(
        text.trim(),
        conversationId ?? undefined,
        undefined,
        latitude,
        longitude,
      )

      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString(),
        sources: response.sources,
        facility_data: response.facility_data,
      }

      setMessages((prev) => [...prev, assistantMsg])
      setConversationId(response.conversation_id)
    } catch (error) {
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading, conversationId])

  const resetConversation = useCallback(async () => {
    if (!conversationId) return
    try {
      await apiResetConversation(conversationId)
      setConversationId(null)
      setMessages([])
    } catch {
      console.error('Failed to reset conversation')
    }
  }, [conversationId])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isLoading,
    conversationId,
    sendMessage,
    resetConversation,
    clearMessages,
  }
}
