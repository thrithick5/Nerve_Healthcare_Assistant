import { useState } from 'react'
import type { ChatMessage } from '../types'
import { formatTimestamp, copyToClipboard } from '../utils/helpers'
import type { Source } from '../types'
import { FormattedMarkdown } from './FormattedMarkdown'
import { FacilityRecommendations } from './FacilityRecommendations'

interface MessageBubbleProps {
  message: ChatMessage
  onShowSources?: (sources: Source[]) => void
}

export function MessageBubble({ message, onShowSources }: MessageBubbleProps) {
  const [showCopy, setShowCopy] = useState(false)
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-4 py-1`}>
      <div
        className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[80%]`}
        onMouseEnter={() => setShowCopy(true)}
        onMouseLeave={() => setShowCopy(false)}
      >
        <div
          className={`${isUser ? 'msg-user' : 'msg-assistant'} ${
            message.role === 'system' ? 'bg-gray-100 text-gray-500 border border-gray-200' : ''
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
              {message.content}
            </p>
          ) : (
            <FormattedMarkdown content={message.content} />
          )}
        </div>

        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-gray-400">
            {formatTimestamp(message.timestamp)}
          </span>
          {showCopy && !isUser && (
            <button
              onClick={() => copyToClipboard(message.content)}
              className="text-xs text-gray-400 hover:text-primary-500 transition-colors"
              title="Copy message"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </button>
          )}
          {message.sources && message.sources.length > 0 && (
            <button
              onClick={() => onShowSources?.(message.sources!)}
              className="text-xs text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1 transition-colors"
              title="View medical sources"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              {message.sources.length} sources
            </button>
          )}
        </div>
        {!isUser && message.facility_data && (
          <FacilityRecommendations facilityData={message.facility_data} />
        )}
      </div>
    </div>
  )
}
