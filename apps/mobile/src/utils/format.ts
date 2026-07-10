export function formatScore(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return undefined;
  }

  return value.toFixed(2);
}

export function formatPercent(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return undefined;
  }

  return `${Math.round(value * 100)}%`;
}

export function formatBytes(value: number | undefined) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return undefined;
  }

  if (value < 1024) {
    return `${value} B`;
  }

  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }

  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatDate(value: string | undefined) {
  if (!value) {
    return undefined;
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return undefined;
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function compactOrigin(value: string | undefined) {
  if (!value) {
    return undefined;
  }

  return value.includes(':') ? value.split(':').at(-1) : value;
}
