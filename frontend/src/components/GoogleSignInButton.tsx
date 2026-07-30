import { useRef } from 'react'
import { CredentialResponse, GoogleLogin } from '@react-oauth/google'

type GoogleSignInButtonProps = {
  onSuccess: (response: CredentialResponse) => void | Promise<void>
  onError: () => void
  label?: string
}

export function GoogleSignInButton({
  onSuccess,
  onError,
  label = 'Google',
}: GoogleSignInButtonProps) {
  const hiddenButtonRef = useRef<HTMLDivElement>(null)

  const handleClick = () => {
    const trigger =
      hiddenButtonRef.current?.querySelector<HTMLElement>('div[role="button"]') ??
      hiddenButtonRef.current?.querySelector<HTMLElement>('iframe')

    trigger?.click()
  }

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={handleClick}
        className="w-full rounded-xl border border-gray-300 bg-white px-4 py-4 text-center text-xl font-semibold text-gray-900 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-300 focus:ring-offset-2 dark:border-[#383838] dark:bg-white dark:text-gray-900 dark:hover:bg-gray-50"
      >
        {label}
      </button>

      <div
        ref={hiddenButtonRef}
        className="pointer-events-none absolute h-0 w-0 overflow-hidden opacity-0"
        aria-hidden="true"
      >
        <GoogleLogin
          onSuccess={onSuccess}
          onError={onError}
          theme="outline"
          size="large"
          text="continue_with"
        />
      </div>
    </div>
  )
}
