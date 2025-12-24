import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/providers/auth-provider';

export function LandingPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="flex flex-col min-h-screen bg-gray-950">
      {/* Header */}
      <header className="p-6 border-b border-gray-800/50">
        <div className="flex items-center justify-between mx-auto max-w-7xl">
          <Link to="/" className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-linear-to-br from-blue-500 to-blue-600">
              <span className="text-sm font-bold text-white">L</span>
            </div>
            <span className="text-xl font-bold text-white">LapEvo</span>
          </Link>
          <div className="flex items-center gap-4">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button>Go to Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="ghost">Sign in</Button>
                </Link>
                <Link to="/register">
                  <Button>Get Started</Button>
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex items-center justify-center flex-1 px-4">
        <div className="max-w-3xl space-y-8 text-center">
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl">
              Evolve Your
              <span className="text-transparent bg-clip-text bg-linear-to-r from-blue-400 to-blue-600"> Lap Times</span>
            </h1>
            <p className="max-w-2xl mx-auto text-xl leading-relaxed text-gray-400">
              AI-powered telemetry analysis for iRacing. Compare laps, identify braking zones,
              and get actionable insights to shave seconds off your times.
            </p>
          </div>

          <div className="flex flex-col items-center justify-center gap-4 pt-4 sm:flex-row">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button size="lg" className="px-8">
                  Go to Dashboard
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/register">
                  <Button size="lg" className="px-8">
                    Start Free
                  </Button>
                </Link>
                <Link to="/login">
                  <Button variant="outline" size="lg">
                    Sign in to Dashboard
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 gap-6 pt-12 text-left sm:grid-cols-3">
            <div className="p-4 border border-gray-800 rounded-lg bg-gray-900/50">
              <div className="mb-2 font-semibold text-blue-400">Telemetry Analysis</div>
              <p className="text-sm text-gray-400">
                Deep dive into throttle, brake, and steering inputs frame by frame.
              </p>
            </div>
            <div className="p-4 border border-gray-800 rounded-lg bg-gray-900/50">
              <div className="mb-2 font-semibold text-blue-400">Lap Comparison</div>
              <p className="text-sm text-gray-400">
                Compare your laps side-by-side to find where you're losing time.
              </p>
            </div>
            <div className="p-4 border border-gray-800 rounded-lg bg-gray-900/50">
              <div className="mb-2 font-semibold text-blue-400">Corner Analysis</div>
              <p className="text-sm text-gray-400">
                Identify braking points and apex speeds for every corner.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-sm text-center text-gray-500 border-t border-gray-800/50">
        LapEvo - Evolve your driving.
      </footer>
    </div>
  );
}
