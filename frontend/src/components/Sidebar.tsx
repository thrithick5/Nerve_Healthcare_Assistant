import { useState } from 'react'
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
        className={`fixed lg:relative z-40 h-full transition-all duration-300 flex flex-col ${
          isOpen ? 'w-72' : 'w-0 overflow-hidden border-none'
        } ${dark ? 'bg-[#171717] border-r border-[#2f2f2f]' : 'bg-gray-50 border-r border-gray-200'}`}
      >
        {isOpen && (
          <>
            {/* Header */}
            <div className="flex items-center justify-between p-3 gap-2">
              <button
                onClick={onNewChat}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors w-full ${
                  dark
                    ? 'border border-[#383838] hover:bg-[#2f2f2f] text-neutral-100'
                    : 'border border-gray-200 hover:bg-gray-100 text-gray-800'
                }`}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </button>
              <button
                onClick={onToggle}
                className={`p-2 rounded-xl transition-colors shrink-0 ${
                  dark ? 'hover:bg-[#2f2f2f] text-neutral-400' : 'hover:bg-gray-200 text-gray-500'
                }`}
                title="Collapse sidebar"
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
                className={`w-full px-3 py-2 rounded-xl text-sm ${
                  dark
                    ? 'bg-[#212121] border border-[#383838] text-white placeholder-neutral-500 focus:border-neutral-500 focus:outline-none'
                    : 'bg-white border border-gray-200 text-gray-800 placeholder-gray-400 focus:outline-none'
                }`}
              />
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto px-2 scrollbar">
              {filteredConversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => onSelect(conv.id)}
                  className={`group flex items-center justify-between px-3 py-2.5 rounded-xl cursor-pointer text-sm transition-colors mb-0.5 ${
                    activeId === conv.id
                      ? dark
                        ? 'bg-[#2f2f2f] text-white'
                        : 'bg-gray-200 text-gray-900'
                      : dark
                      ? 'text-neutral-300 hover:bg-[#212121]'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  <span className="truncate flex-1">{conv.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      onDelete(conv.id)
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-red-500 hover:text-white transition-all"
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
            <div className={`p-3 border-t ${dark ? 'border-[#2f2f2f]' : 'border-gray-200'}`}>
              {/* Theme Switcher */}
              <div className="relative mb-2">
                <button
                  onClick={() => setShowThemeMenu(!showThemeMenu)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm w-full transition-colors ${
                    dark ? 'hover:bg-[#2f2f2f] text-neutral-300' : 'hover:bg-gray-200 text-gray-600'
                  }`}
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
                  <div
                    className={`absolute bottom-full left-0 right-0 mb-1 rounded-xl shadow-lg overflow-hidden ${
                      dark ? 'bg-[#212121] border border-[#383838]' : 'bg-white border border-gray-200'
                    }`}
                  >
                    {(['light', 'dark', 'system'] as Theme[]).map((t) => (
                      <button
                        key={t}
                        onClick={() => {
                          setTheme(t)
                          setShowThemeMenu(false)
                        }}
                        className={`w-full text-left px-4 py-2.5 text-sm ${
                          theme === t
                            ? 'bg-blue-600 text-white'
                            : dark
                            ? 'text-neutral-300 hover:bg-[#2f2f2f]'
                            : 'text-gray-700 hover:bg-gray-100'
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
                  className={`flex items-center gap-3 px-3 py-2.5 rounded-xl w-full transition-colors ${
                    dark ? 'hover:bg-[#2f2f2f] text-white' : 'hover:bg-gray-200 text-gray-800'
                  }`}
                >
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white text-sm font-medium">
                    {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div className="text-left flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{user?.full_name || user?.username || 'User'}</p>
                    <p className={`text-xs truncate ${dark ? 'text-neutral-400' : 'text-gray-500'}`}>
                      {user?.email}
                    </p>
                  </div>
                </button>
                {showUserMenu && (
                  <div
                    className={`absolute bottom-full left-0 right-0 mb-1 rounded-xl shadow-lg overflow-hidden ${
                      dark ? 'bg-[#212121] border border-[#383838]' : 'bg-white border border-gray-200'
                    }`}
                  >
                    <button
                      onClick={onLogout}
                      className={`w-full text-left px-4 py-2.5 text-sm ${
                        dark ? 'text-red-400 hover:bg-[#2f2f2f]' : 'text-red-600 hover:bg-gray-100'
                      }`}
                    >
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </aside>
    </>
  )
}
