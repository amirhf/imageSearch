export type RouterStats = {
  local: number
  cloud: number
}

export type LatencyHistogram = {
  buckets: { le: number; value: number }[]
  sum: number
  count: number
}

export type MetricsSummary = {
  router: RouterStats
  latency: LatencyHistogram
}

const num = (s: string) => Number(s)

export function parsePrometheusText(text: string): MetricsSummary {
  let local = 0
  let cloud = 0
  const buckets: { le: number; value: number }[] = []
  let sum = 0
  let count = 0

  const lines = text.split(/\r?\n/)
  for (const line of lines) {
    if (!line || line.startsWith('#')) continue

    // router counters
    if (line.startsWith('router_local_total')) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) local = num(parts[1])
      continue
    }
    if (line.startsWith('router_cloud_total')) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) cloud = num(parts[1])
      continue
    }

    // latency histogram
    if (line.startsWith('request_latency_ms_bucket')) {
      // request_latency_ms_bucket{le="200"} 12
      const m = line.match(/le="([^"]+)"\}\s+([+-]?[0-9.]+(?:e[+-]?[0-9]+)?)/i)
      if (m) {
        const leStr = m[1]
        const v = num(m[2])
        const le = leStr.toLowerCase() === '+inf' || leStr.toLowerCase() === 'inf' ? Number.POSITIVE_INFINITY : num(leStr)
        buckets.push({ le, value: v })
      }
      continue
    }
    if (line.startsWith('request_latency_ms_sum')) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) sum = num(parts[1])
      continue
    }
    if (line.startsWith('request_latency_ms_count')) {
      const parts = line.trim().split(/\s+/)
      if (parts.length >= 2) count = num(parts[1])
      continue
    }
  }

  buckets.sort((a, b) => (a.le === b.le ? 0 : a.le < b.le ? -1 : 1))

  return {
    router: { local, cloud },
    latency: { buckets, sum, count },
  }
}
