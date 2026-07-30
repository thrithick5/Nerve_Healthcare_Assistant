import { useState, useRef, useEffect, useCallback } from 'react'
import type { ChatMessage } from '../types'
import { FormattedMarkdown } from './FormattedMarkdown'
import { isUploadedFileSource } from '../utils/helpers'

interface PendingFile {
  file: File
  preview: string
  type: 'image' | 'pdf' | 'text'
  id: string
}

interface ChatInterfaceProps {
  messages: ChatMessage[]
  isLoading: boolean
  onSend: (message: string) => Promise<void>
  onToggleSidebar: () => void
  resolvedTheme: 'light' | 'dark'
  hasConversation: boolean
  sidebarOpen: boolean
  onUploadFile: (files: FileList) => void
  pendingFiles: PendingFile[]
  onRemoveFile: (fileId: string) => void
}

export function ChatInterface({
  messages,
  isLoading,
  onSend,
  onToggleSidebar,
  resolvedTheme,
  sidebarOpen,
  onUploadFile,
  pendingFiles,
  onRemoveFile,
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const dark = resolvedTheme === 'dark'
  const fileInputRef = useRef<HTMLInputElement>(null)
  const hasFiles = pendingFiles.length > 0

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return
    onUploadFile(files)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [onUploadFile])

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading, scrollToBottom])

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = input.trim()
    if (!trimmed && !hasFiles) return
    if (isLoading) return
    setInput('')
    await onSend(trimmed)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className={`flex-1 flex flex-col min-w-0 h-full ${dark ? 'bg-[#212121]' : 'bg-white'}`}>
      <div className={`flex items-center gap-3 px-4 py-3 border-b ${dark ? 'border-[#2f2f2f] bg-[#212121]' : 'border-gray-200 bg-white'}`}>

        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className={`p-2 rounded-xl transition-colors ${dark ? 'hover:bg-[#2f2f2f] text-neutral-400' : 'hover:bg-gray-100 text-gray-500'}`}
            title="Open sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}
        <h2 className={`text-base font-semibold ${dark ? 'text-neutral-100' : 'text-gray-800'}`}>
          Nerve Healthcare Assistant
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar">
        {messages.length === 0 && !isLoading ? (
          <div className="flex items-center justify-center h-full px-4">
            <div className="text-center max-w-lg">
              <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 ${dark ? 'bg-[#2f2f2f]' : 'bg-blue-50'}`}>
                <svg className={`w-8 h-8 ${dark ? 'text-blue-400' : 'text-blue-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h2 className={`text-2xl font-bold mb-2 ${dark ? 'text-white' : 'text-gray-800'}`}>Nerve Healthcare Assistant</h2>
              <p className={`text-sm mb-6 ${dark ? 'text-neutral-400' : 'text-gray-500'}`}>
                Ask me about medical health. I answer using trusted medical knowledge.
              </p>
              <div className="grid grid-cols-2 gap-2">
                {[
                  'What are the symptoms of diabetes?',
                  'How to manage high blood pressure?',
                  'Is fasting safe for everyone?',
                  'What to eat for a sore throat?',
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(example)}
                    className={`text-left px-4 py-3 text-sm rounded-xl border transition-colors ${dark ? 'border-[#383838] text-neutral-300 hover:border-neutral-500 hover:bg-[#2f2f2f]' : 'border-gray-200 text-gray-600 hover:border-blue-300 hover:bg-blue-50'}`}
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-5 py-3 ${msg.role === 'user' ? (dark ? 'bg-[#2f2f2f] text-neutral-100' : 'bg-gray-100 text-gray-900') : dark ? 'text-neutral-100' : 'text-gray-800'}`}
                >
                  {msg.role === 'user' ? (
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                      {msg.files && msg.files.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {msg.files.map((f, i) => (
                            f.type === 'image' ? (
                              <img
                                key={i}
                                src={f.url}
                                alt={f.name}
                                className="w-20 h-20 rounded-lg object-cover bg-black/10"
                              />
                            ) : (
                              <div key={i} className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-black/10 text-xs">
                                <svg className="w-3.5 h-3.5 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                  <path d="M4 18h12V6L8 2H4a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                <span className="truncate max-w-24">{f.name}</span>
                              </div>
                            )
                          ))}
                        </div>
                      )}
                      {msg.content}
                    </div>
                  ) : (
                    <>
                      <FormattedMarkdown content={msg.content} dark={dark} />
                      {(() => {
                        const displaySources = msg.sources?.filter(s => !isUploadedFileSource(s)) ?? []
                        return displaySources.length > 0 ? (
                        <div className={`mt-3 pt-3 border-t ${dark ? 'border-[#383838]' : 'border-gray-200'}`}>
                          <div className={`text-xs font-semibold mb-1.5 ${dark ? 'text-neutral-400' : 'text-gray-500'}`}>Sources:</div>
                          <div className="space-y-1">
                            {displaySources.map((src, i) => (
                              <div key={i} className="text-xs">
                                {src.url ? (
                                  <a
                                    href={src.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className={`inline-flex items-center gap-1 hover:underline ${dark ? 'text-blue-400' : 'text-blue-600'}`}
                                  >
                                    <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                    {src.title}
                                  </a>
                                ) : (
                                  <span className={`${dark ? 'text-neutral-400' : 'text-gray-500'}`}>{src.title}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null})()}
                    </>
                  )}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="flex justify-start">
                <div className={`px-5 py-3 ${dark ? '' : ''}`}>
                  <div className="flex items-center gap-1.5">
                    <span className={`typing-dot ${dark ? 'bg-neutral-400' : 'bg-gray-500'}`} />
                    <span className={`typing-dot ${dark ? 'bg-neutral-400' : 'bg-gray-500'}`} />
                    <span className={`typing-dot ${dark ? 'bg-neutral-400' : 'bg-gray-500'}`} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="px-4 pb-4 pt-2">
        <div className="max-w-3xl mx-auto">
          {hasFiles && (
            <div className={`mb-3 p-3 rounded-xl border ${dark ? 'bg-[#2f2f2f] border-[#383838]' : 'bg-gray-50 border-gray-200'}`}>
              <div className={`text-xs font-medium mb-2 ${dark ? 'text-neutral-300' : 'text-gray-600'}`}>
                {pendingFiles.length} file(s) — press Enter to send with your question
              </div>
              <div className="flex flex-wrap gap-2">
                {pendingFiles.map((pf) => (
                  <div
                    key={pf.id}
                    className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg ${dark ? 'bg-[#383838]' : 'bg-gray-200'}`}
                  >
                    {pf.type === 'image' && pf.preview && (
                      <img src={pf.preview} alt="" className="w-8 h-8 object-cover rounded" />
                    )}
                    {pf.type === 'pdf' && (
                      <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 18h12V6L8 2H4a2 2 0 00-2 2v12a2 2 0 002 2zM12 18h2V9h-2V18z" />
                      </svg>
                    )}
                    <span className={`text-xs truncate max-w-28 ${dark ? 'text-neutral-200' : 'text-gray-700'}`}>{pf.file.name}</span>
                    <button
                      onClick={() => onRemoveFile(pf.id)}
                      className="text-red-500 hover:text-red-700 ml-0.5"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className={`flex items-end gap-2 rounded-2xl border p-2 ${dark ? 'border-[#383838] bg-[#2f2f2f]' : 'border-gray-200 bg-gray-50'}`}
          >
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-gray-500 hover:text-gray-700 dark:text-neutral-400 dark:hover:text-neutral-200 transition-colors rounded-xl hover:bg-gray-200 dark:hover:bg-[#383838]"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.121 8.121L20 13" />
              </svg>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.txt"
              onChange={handleFileUpload}
              className="hidden"
            />
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasFiles ? 'Ask about the uploaded files...' : 'Ask a medical question...'}
              rows={1}
              className={`flex-1 resize-none bg-transparent px-3 py-2 text-sm focus:outline-none ${dark ? 'text-white placeholder-neutral-500' : 'text-gray-800 placeholder-gray-400'}`}
            />
            <button
              type="submit"
              disabled={(!input.trim() && !hasFiles) || isLoading}
              className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-all ${
                (!input.trim() && !hasFiles) || isLoading
                  ? dark
                    ? 'bg-[#2f2f2f] text-neutral-500 cursor-not-allowed'
                    : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : dark
                  ? 'bg-white text-black hover:bg-neutral-200 active:scale-95'
                  : 'bg-black text-white hover:bg-gray-800 active:scale-95'
              }`}
              title="Send message"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19V5m0 0l-7 7m7-7l7 7" />
              </svg>
            </button>
          </form>
          <p className={`text-center text-xs mt-2 ${dark ? 'text-neutral-500' : 'text-gray-400'}`}>
            For informational purposes only. Always consult a healthcare professional.
          </p>
        </div>
      </div>
    </div>
  )
}
