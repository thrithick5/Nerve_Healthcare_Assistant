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
        className="w-full rounded-xl border border-border-subtle bg-surface px-4 py-3 text-center text-sm font-medium text-text-primary transition-colors hover:bg-surface-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/80 focus-visible:ring-offset-2 focus-visible:ring-offset-bg shadow-subtle"
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
