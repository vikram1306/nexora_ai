import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Nexora AI | Enterprise Intelligence AI Operating System',
  description: 'Enterprise Intelligence. Autonomous Decisions. Nexora AI is an AI Operating System that turns company datasets into continuous executive intelligence.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-obsidian-900 text-white min-h-screen selection:bg-accent-cyan/30 selection:text-accent-cyan">
        {children}
      </body>
    </html>
  )
}
