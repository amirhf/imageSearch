export const qk = {
  search: (q: string, k: number) => ['search', q, k] as const,
  image: (id: string) => ['image', id] as const,
}
