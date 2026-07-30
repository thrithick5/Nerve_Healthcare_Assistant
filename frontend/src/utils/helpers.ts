export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`
}

export function formatTimestamp(date?: Date | string): string {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date
  return isNaN(d.getTime()) ? '' : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function truncateText(text: string, maxLength: number = 150): string {
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trimEnd() + '...'
}

export function getInitials(name: string): string {
  const words = name.split(' ')
  if (words.length >= 2) {
    return words[0][0] + words[1][0]
  }
  return name.substring(0, 2).toUpperCase()
}

export function isAssistantMessage(role: string): boolean {
  return role === 'assistant'
}

export function isUserMessage(role: string): boolean {
  return role === 'user'
}

export function isUploadedFileSource(source: { source?: string; title?: string }): boolean {
  if (source.source && (source.source.startsWith('image:') || source.source.startsWith('pdf:') || source.source.startsWith('text:'))) {
    return true
  }
  return false
}

export function formatSourceContent(content: string): string {
  return content.replace(/\n{3,}/g, '\n\n').trim()
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text)
}
