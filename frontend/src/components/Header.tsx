import type { ReactNode } from 'react'

interface HeaderProps {
  title: string
  subtitle?: string
  rightSlot?: ReactNode
}

export function Header({ title, subtitle, rightSlot }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white/90 backdrop-blur-sm">
      <div>
        <h1 className="text-xl font-semibold text-gray-800">{title}</h1>
        {subtitle && (
          <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
        )}
      </div>
      {rightSlot && <div>{rightSlot}</div>}
    </header>
  )
}
