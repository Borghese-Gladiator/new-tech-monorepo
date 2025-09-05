import { ReactNode } from 'react';

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow p-4 mb-6">
        <h1 className="text-2xl font-bold">MCP Dashboard</h1>
      </header>
      <main className="max-w-5xl mx-auto px-4">{children}</main>
    </div>
  );
}
