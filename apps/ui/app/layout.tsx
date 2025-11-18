import './globals.css'
import { ReactNode } from 'react'
import { Providers } from './providers'
import { UserMenu } from '@/components/UserMenu'

export const metadata = {
  title: 'Image Search',
  description: 'Semantic search with local vs cloud routing badges'
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900" suppressHydrationWarning>
        <Providers>
          <div className="mx-auto max-w-7xl p-4">
            <header className="mb-6 flex items-center justify-between">
              <a href="/" className="text-sm font-medium hover:underline" aria-label="Go to home">Image Search</a>
              <nav className="flex items-center gap-6">
                <div className="flex items-center gap-3 text-sm">
                  <a href="/" className="hover:underline">Home</a>
                  <a href="/upload" className="hover:underline">Upload</a>
                  <a href="/library" className="hover:underline">Library</a>
                  <a href="/explore" className="hover:underline">Explore</a>
                  <a href="/metrics" className="hover:underline">Metrics</a>
                </div>
                <UserMenu />
              </nav>
            </header>
            {children}
          </div>
        </Providers>
      </body>
    </html>
  )
}
