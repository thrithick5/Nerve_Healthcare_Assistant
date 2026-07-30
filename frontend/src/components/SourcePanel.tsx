import type { Source } from '../types'
import { formatSourceContent, isUploadedFileSource } from '../utils/helpers'

interface SourcePanelProps {
  sources: Source[]
  isOpen: boolean
  onClose: () => void
}

export function SourcePanel({ sources, isOpen, onClose }: SourcePanelProps) {
  const filteredSources = sources.filter(s => !isUploadedFileSource(s))
  if (!isOpen || filteredSources.length === 0) return null

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white border-l border-gray-200 shadow-xl z-50 flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h3 className="font-semibold text-gray-800">Sources</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar p-4 space-y-3">
        {filteredSources.map((source, index) => (
          <div key={index} className="source-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-primary-700 text-xs uppercase tracking-wide">
                {source.title}
              </span>
              <span className="text-xs text-gray-400">
                {Math.round(source.relevance_score * 100)}% match
              </span>
            </div>
            <p className="text-gray-600 text-xs leading-relaxed">
              {formatSourceContent(source.content)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
