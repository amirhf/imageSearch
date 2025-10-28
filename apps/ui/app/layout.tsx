import './globals.css'
import { ReactNode } from 'react'
import { Providers } from './providers'

export const metadata = {
  title: 'Image Search',
  description: 'Semantic search with local vs cloud routing badges'
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900">
        <Providers>
          <div className="mx-auto max-w-7xl p-4">{children}</div>
        </Providers>
      </body>
    </html>
  )
}
