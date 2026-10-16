import { useState, useRef, useEffect, useCallback } from 'react'
import type { ChatMessage } from '../types'
import { FormattedMarkdown } from './FormattedMarkdown'
import { FacilityRecommendations } from './FacilityRecommendations'
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
  onRetry: () => void
  onToggleSidebar: () => void
  resolvedTheme: 'light' | 'dark'
  hasConversation: boolean
  sidebarOpen: boolean
  onUploadFile: (files: FileList) => void
  pendingFiles: PendingFile[]
  onRemoveFile: (fileId: string) => void
}

type ErrorKind = 'tier' | 'busy' | 'network' | 'generic'

function classifyError(content: string): ErrorKind {
  if (/tier_not_allowed|not available on the.*plan|MISTRAL_MODEL/i.test(content)) return 'tier'
  if (/rate.?limit|capacity|overloaded|busy right now|30 seconds|status 429|raw_status_code|code.{0,5}(1300|3505)|\b503\b/i.test(content)) return 'busy'
  if (/network error|check your connection|failed to fetch|load failed|waking up/i.test(content)) return 'network'
  return 'generic'
}

function cleanErrorContent(content: string, kind: ErrorKind): string {
  // Never show raw SDK/JSON payloads (e.g. {"object":"error",...}) in the UI.
  if (/"object"\s*:\s*"error"|raw_status_code|tier_not_allowed/i.test(content)) {
    if (kind === 'tier') return 'The configured AI model is not available on the current plan.'
    if (kind === 'busy') return 'The AI service is busy right now (rate limit / capacity).'
    return 'The AI service returned an error.'
  }
  return content
}

const ERROR_HINT: Record<ErrorKind, string> = {
  tier: 'Admin: set MISTRAL_MODEL to mistral-small-latest on Render and redeploy.',
  busy: 'Quota resets every minute — the retry button unlocks automatically.',
  network: 'The free-tier server may be waking up (can take ~50s) or your connection dropped. Hit Retry.',
  generic: 'Please try again.',
}

const RETRY_BUTTON_CLASS =
  'mt-3 inline-flex items-center gap-1.5 px-3.5 py-2 rounded-full text-[13px] font-medium bg-surface-elevated border border-border text-text-primary shadow-subtle transition-all hover:border-accent/50 active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed'

// Cooldown retry: hammering Retry during a rate limit keeps the per-minute
// quota exhausted longer. The button unlocks on its own after 30s.
function BusyRetryButton({ onRetry, disabled }: { onRetry: () => void; disabled: boolean }) {
  const [wait, setWait] = useState(30)
  useEffect(() => {
    if (wait <= 0) return
    const t = setTimeout(() => setWait((w) => w - 1), 1000)
    return () => clearTimeout(t)
  }, [wait])
  const locked = wait > 0
  return (
    <button onClick={onRetry} disabled={disabled || locked} className={RETRY_BUTTON_CLASS}>
      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M5 9a8 8 0 0114-3m2 7a8 8 0 01-14 3" />
      </svg>
      {locked ? `Retry in ${wait}s` : 'Retry'}
    </button>
  )
}

function isErrorMessage(content: string): boolean {
  return /encountered an error|model unavailable|AI service error|rate.?limit|capacity|busy right now|network error|check your connection|failed to fetch|waking up|unexpected error/i.test(content)
}

const SUGGESTIONS = [
  {
    title: 'Symptoms guide',
    prompt: 'What are the symptoms of diabetes?',
  },
  {
    title: 'Manage condition',
    prompt: 'How to manage high blood pressure?',
  },
  {
    title: 'Nutrition advice',
    prompt: 'What to eat for a sore throat?',
  },
  {
    title: 'Find care',
    prompt: 'Find a hospital near me',
  },
]

export function ChatInterface({
  messages,
  isLoading,
  onSend,
  onRetry,
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
  const [isListening, setIsListening] = useState(false)
  const recognitionRef = useRef<any>(null)
  const voiceBaseRef = useRef<string>('')

  const toggleVoice = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) {
      alert('Voice input is not supported in this browser. Please try Chrome or Edge.')
      return
    }
    if (isListening) {
      recognitionRef.current?.stop()
      setIsListening(false)
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.continuous = false
    voiceBaseRef.current = inputRef.current?.value ?? ''
    recognition.onresult = (event: any) => {
      let transcript = ''
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript
      }
      const base = voiceBaseRef.current
      setInput((base ? base + ' ' : '') + transcript.trim())
    }
    recognition.onend = () => setIsListening(false)
    recognition.onerror = () => setIsListening(false)
    recognition.start()
    recognitionRef.current = recognition
    setIsListening(true)
  }, [isListening])

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

  const canSend = (input.trim() || hasFiles) && !isLoading

  return (
    <div className="flex-1 flex flex-col min-w-0 h-full bg-bg">
      {/* Top bar — minimal, Claude-like */}
      <header className="flex items-center gap-3 px-4 sm:px-6 py-3 border-b border-border bg-bg/80 backdrop-blur supports-[backdrop-filter]:bg-bg/60 sticky top-0 z-10">
        {!sidebarOpen && (
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-xl transition-colors text-text-tertiary hover:text-text-secondary hover:bg-surface-secondary active:scale-[0.98]"
            title="Open sidebar"
            aria-label="Open sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        )}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-accent text-accent-foreground flex items-center justify-center text-sm font-semibold shrink-0" aria-hidden="true">
            N
          </div>
          <h2 className="text-[15px] font-semibold text-text-primary truncate">
            Nerve
          </h2>
          <span className="hidden sm:inline text-xs text-text-tertiary truncate">
            Healthcare Assistant
          </span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar" role="log" aria-live="polite" aria-label="Conversation">
        {messages.length === 0 && !isLoading ? (
          <div className="flex items-center justify-center min-h-full px-4 py-10">
            <div className="text-center max-w-2xl w-full animate-fade-in-up">
              <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5 bg-accent/10 ring-1 ring-accent/25 shadow-subtle" aria-hidden="true">
                <span className="text-2xl font-semibold text-accent">N</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-semibold mb-3 text-text-primary tracking-tight text-balance">
                How can I help you today?
              </h2>
              <p className="text-sm sm:text-[15px] mb-8 text-text-secondary leading-relaxed max-w-md mx-auto">
                Ask about symptoms, conditions, medications, or find care nearby. Answers use trusted medical knowledge.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left max-w-xl mx-auto">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.prompt}
                    onClick={() => setInput(s.prompt)}
                    className="group px-4 py-3.5 rounded-2xl border border-border bg-surface text-left transition-all hover:border-accent/40 hover:shadow-soft hover:-translate-y-px active:translate-y-0 active:scale-[0.995]"
                  >
                    <span className="block text-[13px] font-medium text-text-primary mb-0.5">{s.title}</span>
                    <span className="block text-[13px] text-text-tertiary group-hover:text-text-secondary truncate">{s.prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 sm:px-6 py-6 space-y-6">
            {messages.map((msg) => {
              const isError = msg.role === 'assistant' && isErrorMessage(msg.content)
              const errorKind: ErrorKind = isError ? classifyError(msg.content) : 'generic'
              if (msg.role === 'user') {
                return (
                  <div key={msg.id} className="flex justify-end animate-fade-in-up">
                    <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl rounded-br-md px-4 sm:px-5 py-3 bg-surface-secondary text-text-primary shadow-subtle">
                      {msg.files && msg.files.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {msg.files.map((f, i) => (
                            f.type === 'image' ? (
                              <img
                                key={i}
                                src={f.url}
                                alt={f.name}
                                className="w-20 h-20 rounded-xl object-cover bg-black/10"
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
                      <div className="text-[15px] leading-relaxed whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                )
              }
              // Assistant — plain, Claude-style (no bubble), with error card variant
              return (
                <div key={msg.id} className="flex justify-start animate-fade-in-up">
                  <div className="w-full min-w-0">
                    {isError ? (
                      <div className="rounded-2xl border border-danger/25 bg-danger/10 px-4 sm:px-5 py-4" role="alert">
                        <p className="text-sm font-medium text-text-primary mb-1">Something went wrong</p>
                        <p className="text-sm text-text-secondary leading-relaxed">{cleanErrorContent(msg.content, errorKind)}</p>
                        <p className="text-xs text-text-tertiary mt-2">{ERROR_HINT[errorKind]}</p>
                        {errorKind === 'busy' ? (
                          <BusyRetryButton key={msg.id} onRetry={onRetry} disabled={isLoading} />
                        ) : (
                          <button
                            onClick={onRetry}
                            disabled={isLoading}
                            className={RETRY_BUTTON_CLASS}
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h5M20 20v-5h-5M5 9a8 8 0 0114-3m2 7a8 8 0 01-14 3" />
                            </svg>
                            Retry
                          </button>
                        )}
                      </div>
                    ) : (
                      <div className="text-[15px] leading-relaxed text-text-primary min-w-0">
                        <FormattedMarkdown content={msg.content} dark={dark} />
                      </div>
                    )}
                    {msg.facility_data && (
                      <FacilityRecommendations facilityData={msg.facility_data} />
                    )}
                    {(() => {
                      const displaySources = msg.sources?.filter(s => !isUploadedFileSource(s)) ?? []
                      return displaySources.length > 0 ? (
                        <div className="mt-3 pt-3 border-t border-border-subtle">
                          <div className="text-xs font-medium mb-1.5 text-text-tertiary">Sources</div>
                          <div className="flex flex-wrap gap-1.5">
                            {displaySources.map((src, i) => (
                              <div key={i} className="text-xs">
                                {src.url ? (
                                  <a
                                    href={src.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-border bg-surface text-text-secondary hover:text-text-primary hover:border-accent/40 transition-colors"
                                  >
                                    <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                    </svg>
                                    <span className="max-w-48 truncate">{src.title}</span>
                                  </a>
                                ) : (
                                  <span className="inline-flex px-2.5 py-1.5 rounded-full border border-border text-text-tertiary">{src.title}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : null
                    })()}
                  </div>
                </div>
              )
            })}

            {isLoading && (
              <div className="flex justify-start" aria-label="Assistant is typing">
                <div className="py-2 animate-fade-in">
                  <div className="flex items-center gap-1.5">
                    <span className="typing-dot bg-text-tertiary" />
                    <span className="typing-dot bg-text-tertiary" />
                    <span className="typing-dot bg-text-tertiary" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Composer — Claude-like pill */}
      <div className="px-4 sm:px-6 pb-4 sm:pb-5 pt-2 bg-gradient-to-t from-bg via-bg to-transparent">
        <div className="max-w-3xl mx-auto">
          {hasFiles && (
            <div className="mb-2.5 p-3 rounded-2xl border border-border bg-surface shadow-subtle animate-scale-in">
              <div className="text-xs font-medium mb-2 text-text-secondary">
                {pendingFiles.length} file(s) — press Enter to send with your question
              </div>
              <div className="flex flex-wrap gap-2">
                {pendingFiles.map((pf) => (
                  <div
                    key={pf.id}
                    className="flex items-center gap-2 pl-1.5 pr-2 py-1.5 rounded-xl bg-surface-secondary border border-border-subtle"
                  >
                    {pf.type === 'image' && pf.preview && (
                      <img src={pf.preview} alt="" className="w-8 h-8 object-cover rounded-lg" />
                    )}
                    {pf.type === 'pdf' && (
                      <svg className="w-4 h-4 shrink-0 text-text-secondary ml-1" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M4 18h12V6L8 2H4a2 2 0 00-2 2v12a2 2 0 002 2zM12 18h2V9h-2V18z" />
                      </svg>
                    )}
                    <span className="text-xs truncate max-w-28 text-text-primary">{pf.file.name}</span>
                    <button
                      onClick={() => onRemoveFile(pf.id)}
                      className="p-1 rounded-md text-text-tertiary hover:text-danger hover:bg-danger/10 transition-colors"
                      aria-label={`Remove ${pf.file.name}`}
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <form
            onSubmit={handleSubmit}
            className="flex items-end gap-1.5 rounded-[28px] border border-border bg-surface-elevated shadow-soft px-2.5 py-2 transition-colors focus-within:border-accent/50"
          >
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-text-tertiary hover:text-text-secondary transition-colors rounded-full hover:bg-surface-secondary active:scale-[0.96]"
              aria-label="Attach files"
              title="Attach files"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.121 8.121L20 13" />
              </svg>
            </button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,.pdf,.txt"
              onChange={handleFileUpload}
              className="hidden"
              aria-hidden="true"
              tabIndex={-1}
            />
            <button
              type="button"
              onClick={toggleVoice}
              title={isListening ? 'Stop listening' : 'Speak your symptoms'}
              aria-label={isListening ? 'Stop listening' : 'Dictate message'}
              aria-pressed={isListening}
              className={`p-2.5 transition-colors rounded-full active:scale-[0.96] ${
                isListening
                  ? 'text-white bg-danger animate-pulse'
                  : 'text-text-tertiary hover:text-text-secondary hover:bg-surface-secondary'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <rect x="9" y="2" width="6" height="12" rx="3" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 10a7 7 0 01-14 0m7 7v4m-4 0h8" />
              </svg>
            </button>
            <label htmlFor="chat-composer" className="sr-only">Ask a medical question</label>
            <textarea
              id="chat-composer"
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasFiles ? 'Ask about the uploaded files...' : 'How can I help you today?'}
              rows={1}
              className="composer-textarea flex-1 resize-none bg-transparent px-2 py-2.5 text-[15px] leading-relaxed text-text-primary placeholder:text-text-tertiary min-h-[44px] max-h-[200px]"
            />
            <button
              type="submit"
              disabled={!canSend}
              className={`w-9 h-9 mb-0.5 rounded-full flex items-center justify-center shrink-0 transition-all active:scale-[0.94] ${
                !canSend
                  ? 'bg-surface-secondary text-text-tertiary cursor-not-allowed'
                  : 'bg-accent text-accent-foreground hover:brightness-110 shadow-soft'
              }`}
              title="Send message"
              aria-label="Send message"
            >
              <svg className="w-4.5 h-4.5 w-[18px] h-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 19V5m0 0l-7 7m7-7l7 7" />
              </svg>
            </button>
          </form>
          <p className="text-center text-[11px] sm:text-xs mt-2.5 text-text-tertiary">
            For informational purposes only. Always consult a healthcare professional.
          </p>
        </div>
      </div>
    </div>
  )
}
