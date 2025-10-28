import Image from 'next/image'
import { OriginBadge } from './OriginBadge'
import { ImageSummary } from '@/lib/types'

export function ImageCard({ item, onOpen }: { item: ImageSummary; onOpen?: (id: string) => void }) {
  return (
    <div className="card-hover overflow-hidden rounded-lg border border-neutral-200 bg-white">
      <button
        className="block w-full text-left"
        onClick={() => onOpen?.(item.id)}
        aria-label={`Open details for image ${item.id}`}
      >
        <div className="relative aspect-square w-full bg-neutral-100">
          {item.thumbnail_url ? (
            <Image
              src={item.thumbnail_url}
              alt={item.caption || 'image'}
              fill
              className="object-cover"
              unoptimized
            />
          ) : (
            <div className="flex h-full items-center justify-center text-neutral-400">No thumbnail</div>
          )}
        </div>
        <div className="space-y-1 p-3">
          <div className="line-clamp-2 text-sm text-neutral-800">{item.caption}</div>
          <div className="flex items-center justify-between">
            <OriginBadge origin={item.origin} confidence={item.confidence} />
            {typeof item.score === 'number' && (
              <span className="text-xs text-neutral-500">{item.score.toFixed(3)}</span>
            )}
          </div>
        </div>
      </button>
    </div>
  )
}
