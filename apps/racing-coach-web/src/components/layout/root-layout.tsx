import { Link, Outlet, useLocation } from 'react-router-dom';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Sessions', href: '/' },
  { name: 'Live', href: '/live' },
  { name: 'Compare', href: '/compare' },
];

export function RootLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 className="text-xl font-bold text-blue-400">
                Racing Coach
              </h1>
              <nav className="flex gap-4">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={cn(
                      'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      location.pathname === item.href
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-400 hover:bg-gray-800/50 hover:text-white'
                    )}
                  >
                    {item.name}
                  </Link>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
