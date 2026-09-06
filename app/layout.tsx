import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Shibuya Life — Small city. Big stories.',
  description: 'Walk, ride and explore a miniature Tokyo. A third-person world built in Blender.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
