"use client"

export default function MetricStat({ label, value, suffix }: { label: string; value: string | number | null; suffix?: string }) {
  const display = value == null ? '—' : typeof value === 'number' ? value.toString() : value
  return (
    <div className="rounded-md border p-4">
      <div className="text-xs uppercase text-neutral-500">{label}</div>
      <div className="text-2xl font-semibold">
        {display}
        {suffix ? <span className="ml-1 text-sm text-neutral-500">{suffix}</span> : null}
      </div>
    </div>
  )
}
