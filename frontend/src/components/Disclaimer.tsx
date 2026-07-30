interface DisclaimerProps {
  text: string
}

export function Disclaimer({ text }: DisclaimerProps) {
  return (
    <div className="flex items-start gap-2 px-4 py-2 bg-amber-50 border border-amber-200 rounded-lg">
      <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-sm text-amber-800 leading-relaxed">{text}</p>
    </div>
  )
}
