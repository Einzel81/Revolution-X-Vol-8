// frontend/app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { LanguageProvider } from '@/components/i18n/LanguageProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Revolution X - AI Gold Trading',
  description: 'Advanced AI-powered gold trading system with Smart Money Concepts',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr" className="dark">
      <body className={inter.className}>
        <LanguageProvider>
          <div className="min-h-screen bg-revolution-dark">{children}</div>
        </LanguageProvider>
      </body>
    </html>
  );
}