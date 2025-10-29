export type MetricSample = {
  name: string
  labels: Record<string, string>
  value: number
}

// Parse Prometheus text exposition format (simple, instant vector)
export function parsePrometheusText(text: string): MetricSample[] {
  const out: MetricSample[] = []
  const lines = text.split(/\r?\n/)
  const re = /^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{([^}]*)\})?\s+([0-9eE+\-.]+)(?:\s+[0-9]+)?$/
  for (const line of lines) {
    const s = line.trim()
    if (!s || s.startsWith('#')) continue
    const m = re.exec(s)
    if (!m) continue
    const [, name, , labelStr, valStr] = m
    const labels: Record<string, string> = {}
    if (labelStr) {
      for (const kv of splitLabels(labelStr)) {
        const eq = kv.indexOf('=')
        if (eq > -1) {
          const k = kv.slice(0, eq).trim()
          const vRaw = kv.slice(eq + 1).trim()
          const v = vRaw.replace(/^"|"$/g, '')
          labels[k] = v
        }
      }
    }
    const value = Number(valStr)
    if (!Number.isFinite(value)) continue
    out.push({ name, labels, value })
  }
  return out
}

function splitLabels(s: string): string[] {
  // split by comma but ignore commas inside quotes
  const parts: string[] = []
  let cur = ''
  let inQ = false
  for (let i = 0; i < s.length; i++) {
    const ch = s[i]
    if (ch === '"') inQ = !inQ
    if (ch === ',' && !inQ) {
      parts.push(cur)
      cur = ''
    } else {
      cur += ch
    }
  }
  if (cur) parts.push(cur)
  return parts
}

export function sumMetric(samples: MetricSample[], metric: string): number {
  return samples
    .filter((s) => s.name === metric)
    .reduce((acc, s) => acc + s.value, 0)
}

export function histogramQuantile(samples: MetricSample[], metric: string, q: number): number | null {
  // Aggregate buckets by `le` across labels
  const buckets = samples.filter((s) => s.name === metric && s.labels && typeof s.labels.le === 'string')
  if (buckets.length === 0) return null
  const agg = new Map<number, number>()
  let total = 0
  for (const b of buckets) {
    const leStr = b.labels.le
    const le = leStr === '+Inf' ? Number.POSITIVE_INFINITY : Number(leStr)
    const prev = agg.get(le) ?? 0
    const next = prev + b.value
    agg.set(le, next)
  }
  // Total is value at +Inf (cumulative)
  total = agg.get(Number.POSITIVE_INFINITY) ?? 0
  if (total <= 0) return null
  // sort thresholds
  const entries = Array.from(agg.entries()).sort((a, b) => a[0] - b[0])
  const target = q * total
  for (const [le, cum] of entries) {
    if (cum >= target) {
      if (!Number.isFinite(le)) return null // cannot return +Inf
      return le
    }
  }
  return null
}
