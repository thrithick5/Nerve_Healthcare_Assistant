import { useState, useEffect, useCallback } from 'react'
import { Sidebar } from '../components/Sidebar'
import { ChatInterface } from '../components/ChatInterface'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import type { Conversation, ChatMessage } from '../types'
import { getConversations, getConversation, sendChatMessage, deleteConversation, uploadFile } from '../services/api'

interface PendingFile {
  file: File
  preview: string
  type: 'image' | 'pdf' | 'text'
  id: string
}

export function ChatPage() {
  const { user, logout } = useAuth()
  const { theme, setTheme, resolvedTheme } = useTheme()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])

  useEffect(() => {
    loadConversations()
  }, [])

  const loadConversations = async () => {
    try {
      const data = await getConversations()
      setConversations(data)
    } catch (err) {
      console.error('Failed to load conversations:', err)
    }
  }

  const handleNewConversation = useCallback(async () => {
    setActiveConversationId(null)
    setMessages([])
  }, [])

  const handleSelectConversation = useCallback(async (id: number) => {
    try {
      const data = await getConversation(id)
      setMessages(data.messages.map((m: any, i: number) => ({
        id: i,
        role: m.role,
        content: m.content,
        created_at: m.created_at,
        sources: m.sources,
      })))
      setActiveConversationId(id)
    } catch (err) {
      console.error('Failed to load conversation:', err)
    }
  }, [])

  const handleDeleteConversation = useCallback(async (id: number) => {
    try {
      await deleteConversation(id)
      setConversations((prev) => prev.filter((c) => c.id !== id))
      if (activeConversationId === id) {
        setActiveConversationId(null)
        setMessages([])
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err)
    }
  }, [activeConversationId])

  const handleUploadFile = useCallback((files: FileList) => {
    const filesToAdd: PendingFile[] = Array.from(files).map(file => ({
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : '',
      type: file.type.startsWith('image/') ? 'image' : file.type === 'application/pdf' ? 'pdf' : 'text',
      id: `${Date.now()}-${Math.random()}`,
    }))
    setPendingFiles(prev => [...prev, ...filesToAdd])
  }, [])

  const handleRemoveFile = useCallback((fileId: string) => {
    setPendingFiles(prev => {
      const file = prev.find(f => f.id === fileId)
      if (file?.preview) URL.revokeObjectURL(file.preview)
      return prev.filter(f => f.id !== fileId)
    })
  }, [])

  // Keywords that signal the user wants nearby facility search
  const LOCATION_KEYWORDS = [
    'near me', 'nearby', 'around me', 'closest', 'nearest', 'close to me',
    'in my area', 'near my location', 'find hospital', 'find clinic',
    'find pharmacy', 'find doctor', 'find a hospital', 'find a clinic',
    'find a pharmacy', 'find a doctor',
  ]

  const needsLocation = (text: string): boolean => {
    const lower = text.toLowerCase()
    return LOCATION_KEYWORDS.some((kw) => lower.includes(kw))
  }

  const requestGeolocation = (): Promise<{ latitude: number; longitude: number } | null> => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null)
        return
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
        () => resolve(null),
        { timeout: 8000, maximumAge: 60000 },
      )
    })
  }

  const handleSendMessage = useCallback(async (message: string) => {
    const filesToUpload = pendingFiles
    const hasFiles = filesToUpload.length > 0

    if (!message.trim() && !hasFiles) return

    if (hasFiles) {
      setPendingFiles([])
    }

    const fileAttachments = hasFiles ? filesToUpload.map(pf => ({
      name: pf.file.name,
      url: pf.preview,
      type: pf.type as 'image' | 'pdf' | 'text',
    })) : undefined

    const userMsg: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: message || `Uploaded ${filesToUpload.length} file(s)`,
      created_at: new Date().toISOString(),
      files: fileAttachments,
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    try {
      const uploadedSources: string[] = []
      for (const pf of filesToUpload) {
        const result = await uploadFile(pf.file, pf.file.name)
        if (result?.source) {
          uploadedSources.push(result.source)
        }
      }

      // Request geolocation if the message has "near me" intent
      let latitude: number | undefined
      let longitude: number | undefined
      if (needsLocation(message)) {
        const coords = await requestGeolocation()
        if (coords) {
          latitude = coords.latitude
          longitude = coords.longitude
        }
      }

      const response = await sendChatMessage(
        message,
        activeConversationId ?? undefined,
        uploadedSources.length > 0 ? uploadedSources : undefined,
        latitude,
        longitude,
      )
      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.reply,
        created_at: new Date().toISOString(),
        sources: response.sources ?? undefined,
        facility_data: response.facility_data,
      }
      setMessages((prev) => [...prev, assistantMsg])
      setActiveConversationId(response.conversation_id)
      await loadConversations()
    } catch (err) {
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }, [activeConversationId, pendingFiles])

  return (
    <div className={`flex h-screen ${resolvedTheme === 'dark' ? 'bg-[#212121]' : 'bg-white'}`}>
      <Sidebar
        conversations={conversations}
        activeId={activeConversationId}
        onSelect={handleSelectConversation}
        onNewChat={handleNewConversation}
        onDelete={handleDeleteConversation}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        theme={theme}
        setTheme={setTheme}
        user={user}
        onLogout={logout}
        resolvedTheme={resolvedTheme}
      />
        <ChatInterface
          messages={messages}
          isLoading={isLoading}
          onSend={handleSendMessage}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          resolvedTheme={resolvedTheme}
          hasConversation={activeConversationId !== null}
          sidebarOpen={sidebarOpen}
          onUploadFile={handleUploadFile}
          pendingFiles={pendingFiles}
          onRemoveFile={handleRemoveFile}
        />
    </div>
  )
}
