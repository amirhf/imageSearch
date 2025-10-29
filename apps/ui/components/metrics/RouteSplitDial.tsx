"use client"

export default function RouteSplitDial({ local, cloud }: { local: number; cloud: number }) {
  const total = Math.max(0, (local || 0) + (cloud || 0))
  const localPct = total > 0 ? Math.round((local / total) * 100) : 0
  const cloudPct = 100 - localPct
  const bg = `conic-gradient(#0a0a0a 0% ${localPct}%, #a3a3a3 ${localPct}% 100%)`
  return (
    <div className="flex items-center gap-4 rounded-md border p-4">
      <div className="relative h-24 w-24 shrink-0 rounded-full" style={{ backgroundImage: bg }} aria-label="Route split donut">
        <div className="absolute inset-2 rounded-full bg-white" />
        <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold">{localPct}%</div>
      </div>
      <div className="text-sm">
        <div className="flex items-center gap-2"><span className="inline-block h-2 w-2 rounded-sm bg-neutral-900" /> Local: {local}</div>
        <div className="flex items-center gap-2"><span className="inline-block h-2 w-2 rounded-sm bg-neutral-400" /> Cloud: {cloud}</div>
      </div>
    </div>
  )
}
