import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface FormattedMarkdownProps {
  content: string
  dark?: boolean
}

export function FormattedMarkdown({ content, dark }: FormattedMarkdownProps) {
  let cleanContent = (content || '').trim()

  // Remove triple-backtick markdown block wrappers if present
  if (/^```(?:markdown|md)?\s*\n/i.test(cleanContent) && cleanContent.endsWith('```')) {
    cleanContent = cleanContent.replace(/^```(?:markdown|md)?\s*\n/i, '').replace(/\n\s*```$/, '')
  }

  // Convert inline double pipes '||' separating table rows into proper newlines '|\n|'
  cleanContent = cleanContent.replace(/\|\|/g, '|\n|')

  // Strip orphan standalone divider/separator lines (e.g. ---, ***, ___, --------, or orphan table dividers)
  cleanContent = cleanContent
    .replace(/^[\s]*([-*_]){3,}[\s]*$/gm, '')
    .replace(/^[\s]*\|?\s*[-:\s]{3,}\s*(?:\|[-:\s]{3,})*\|?[\s]*$/gm, (match) => {
      // Only keep table separator lines if they are within standard markdown table structure
      return match.includes('|') ? match : ''
    })
    .replace(/\n{3,}/g, '\n\n')

  return (
    <div className={`markdown-body text-[15px] leading-relaxed ${dark ? 'text-neutral-100' : 'text-gray-800'}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          hr: () => null,
          table: ({ children }) => (
            <div className="my-4 overflow-x-auto rounded-xl border border-gray-200 dark:border-[#383838]">
              <table className="w-full text-left text-sm border-collapse">{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className={dark ? 'bg-[#2f2f2f] text-white border-b border-[#383838]' : 'bg-gray-100 text-gray-900 border-b border-gray-200'}>
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className={`divide-y ${dark ? 'divide-[#383838]' : 'divide-gray-200'}`}>{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className={`transition-colors ${dark ? 'hover:bg-[#282828]' : 'hover:bg-gray-50'}`}>{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-4 py-3 font-semibold text-xs uppercase tracking-wider">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm align-top leading-relaxed">{children}</td>
          ),
          p: ({ children }) => <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>,
          strong: ({ children }) => (
            <strong className={`font-semibold ${dark ? 'text-white' : 'text-gray-900'}`}>{children}</strong>
          ),
          em: ({ children }) => (
            <em className={`italic ${dark ? 'text-neutral-300' : 'text-gray-700'}`}>{children}</em>
          ),
          h1: ({ children }) => (
            <h1 className={`text-lg font-bold mt-4 mb-2 first:mt-0 ${dark ? 'text-white' : 'text-gray-900'}`}>{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className={`text-base font-bold mt-3 mb-2 first:mt-0 ${dark ? 'text-white' : 'text-gray-900'}`}>{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className={`text-base font-semibold mt-3 mb-1.5 first:mt-0 ${dark ? 'text-white' : 'text-gray-900'}`}>{children}</h3>
          ),
          ul: ({ children }) => <ul className="my-2.5 pl-5 list-disc space-y-1.5">{children}</ul>,
          ol: ({ children }) => <ol className="my-2.5 pl-5 list-decimal space-y-1.5">{children}</ol>,
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,
          blockquote: ({ children }) => (
            <blockquote className={`pl-3 border-l-2 my-2.5 italic ${dark ? 'border-neutral-600 text-neutral-400' : 'border-gray-300 text-gray-600'}`}>
              {children}
            </blockquote>
          ),
          code: ({ children }) => (
            <code className={`px-1.5 py-0.5 rounded text-xs font-mono ${dark ? 'bg-neutral-800 text-blue-300' : 'bg-gray-200 text-blue-800'}`}>
              {children}
            </code>
          ),
        }}
      >
        {cleanContent}
      </ReactMarkdown>
    </div>
  )
}


