import clsx from 'clsx'

export function OriginBadge({ origin, confidence }: { origin?: 'local' | 'cloud'; confidence?: number }) {
  if (!origin) return null
  const label = origin === 'local' ? 'Local' : 'Cloud'
  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        origin === 'local' ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-200' : 'bg-violet-50 text-violet-700 ring-1 ring-violet-200'
      )}
      title={typeof confidence === 'number' ? `${label} • conf=${confidence.toFixed(2)}` : label}
      aria-label={`Caption origin: ${label}${typeof confidence === 'number' ? `, confidence ${confidence.toFixed(2)}` : ''}`}
    >
      {label}
    </span>
  )
}
