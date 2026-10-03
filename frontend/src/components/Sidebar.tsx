import { useState, useEffect, useCallback } from 'react'
import type { Conversation, Theme, User } from '../types'

interface SidebarProps {
  conversations: Conversation[]
  activeId: number | null
  onSelect: (id: number) => void
  onNewChat: () => void
  onDelete: (id: number) => void
  isOpen: boolean
  onToggle: () => void
  theme: Theme
  setTheme: (theme: Theme) => void
  user: User | null
  onLogout: () => void
  resolvedTheme: 'light' | 'dark'
}

export function Sidebar({
  conversations,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  isOpen,
  onToggle,
  theme,
  setTheme,
  user,
  onLogout,
  resolvedTheme,
}: SidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showThemeMenu, setShowThemeMenu] = useState(false)
  const [width, setWidth] = useState(288)
  const [isResizing, setIsResizing] = useState(false)

  const startResizing = useCallback(() => {
    setIsResizing(true)
  }, [])

  const stopResizing = useCallback(() => {
    setIsResizing(false)
  }, [])

  const resize = useCallback((mouseMoveEvent: MouseEvent) => {
    const newWidth = Math.max(200, Math.min(mouseMoveEvent.clientX, 480))
    setWidth(newWidth)
  }, [])

  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', resize)
      window.addEventListener('mouseup', stopResizing)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'col-resize'
    } else {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
    return () => {
      window.removeEventListener('mousemove', resize)
      window.removeEventListener('mouseup', stopResizing)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [isResizing, resize, stopResizing])

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const dark = resolvedTheme === 'dark'

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/60 z-30 lg:hidden" onClick={onToggle} />
      )}

      <aside
        style={{ width: isOpen ? `${width}px` : '0px' }}
        className={`fixed lg:relative z-40 h-full flex flex-col ${
          isResizing ? '' : 'transition-[width] duration-300'
        } ${!isOpen ? 'overflow-hidden border-none' : ''} ${
          dark ? 'bg-surface border-r border-border' : 'bg-surface-secondary border-r border-border'
        }`}
      >
        {isOpen && (
          <>
            {/* Header */}
            <div className="flex items-center justify-between p-3 gap-2">
              <button
                onClick={onNewChat}
                className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors w-full border border-border-subtle bg-surface-elevated text-text-primary shadow-subtle hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg active:scale-[0.995]"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </button>
              <button
                onClick={onToggle}
                className="p-2 rounded-xl transition-colors shrink-0 text-text-tertiary hover:text-text-secondary hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg active:scale-[0.995]"
                title="Collapse sidebar"
                aria-label="Collapse sidebar"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>

            {/* Search */}
            <div className="px-3 mb-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full px-3 py-2 rounded-xl text-sm bg-surface border border-border-subtle text-text-primary placeholder:text-text-tertiary focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg transition-shadow"
                aria-label="Search conversations"
              />
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto px-2 scrollbar">
              {filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => onSelect(conv.id)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-colors mb-0.5 animate-fade-in ${
                    activeId === conv.id
                      ? 'bg-surface-elevated text-text-primary shadow-subtle ring-1 ring-border-subtle'
                      : 'text-text-secondary hover:bg-surface-secondary hover:text-text-primary'
                  }`}
                >
                  <span className="truncate flex-1">{conv.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete(conv.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-danger/10 hover:text-danger text-text-tertiary transition-all focus-visible:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg active:scale-[0.98]"
                    aria-label="Delete conversation"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                </div>
              ))}
            </div>

            {/* Bottom section */}
            <div className="p-3 border-t border-border">
              {/* Theme Switcher */}
              <div className="relative mb-2">
                <button
                  onClick={() => setShowThemeMenu(!showThemeMenu)}
                  className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm w-full transition-colors text-text-secondary hover:text-text-primary hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg active:scale-[0.995]"
                >
                  {resolvedTheme === 'dark' ? (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                      />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                      />
                    </svg>
                  )}
                  {theme.charAt(0).toUpperCase() + theme.slice(1)} Mode
                </button>
                {showThemeMenu && (
                  <div className="absolute bottom-full left-0 right-0 mb-1 rounded-xl shadow-elevated bg-surface-elevated border border-border overflow-hidden animate-scale-in">
                    {(['light', 'dark', 'system'] as Theme[]).map((t) => (
                      <button
                        key={t}
                        onClick={() => {
                          setTheme(t)
                          setShowThemeMenu(false)
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm transition-colors ${
                          theme === t
                            ? 'bg-accent text-accent-foreground'
                            : 'text-text-primary hover:bg-surface-secondary'
                        }`}
                      >
                        {t.charAt(0).toUpperCase() + t.slice(1)}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* User Menu */}
              <div className="relative">
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl w-full transition-colors text-text-primary hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg active:scale-[0.995]"
                >
                  <div className="w-8 h-8 rounded-full bg-accent text-accent-foreground flex items-center justify-center text-sm font-medium shadow-soft">
                    {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div className="text-left flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{user?.full_name || user?.username || 'User'}</p>
                    <p className="text-xs truncate text-text-tertiary">
                      {user?.email}
                    </p>
                  </div>
                </button>
                {showUserMenu && (
                  <div className="absolute bottom-full left-0 right-0 mb-1 rounded-xl shadow-elevated bg-surface-elevated border border-border overflow-hidden animate-scale-in">
                    <button
                      onClick={onLogout}
                      className="w-full text-left px-4 py-2.5 text-sm text-danger hover:bg-danger/10 transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
        {isOpen && (
          <div
            onMouseDown={startResizing}
            className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize z-50 group/handle"
            title="Drag to resize sidebar"
          >
            <div className={`w-0.5 h-full mx-auto transition-colors group-hover/handle:bg-blue-500/80 group-active/handle:bg-blue-600 ${isResizing ? 'bg-blue-500 w-1' : ''}`} />
          </div>
        )}
      </aside>
    </>
  )
}
