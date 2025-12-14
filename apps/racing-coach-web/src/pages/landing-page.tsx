import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';

export function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="p-6 border-b border-gray-800/50">
        <div className="mx-auto max-w-7xl flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">L</span>
            </div>
            <span className="text-xl font-bold text-white">LapEvo</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link to="/register">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-4">
        <div className="max-w-3xl text-center space-y-8">
          <div className="space-y-4">
            <h1 className="text-5xl sm:text-6xl font-bold text-white tracking-tight">
              Evolve Your
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-blue-600"> Lap Times</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto leading-relaxed">
              AI-powered telemetry analysis for iRacing. Compare laps, identify braking zones,
              and get actionable insights to shave seconds off your times.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
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
          </div>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 pt-12 text-left">
            <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
              <div className="text-blue-400 font-semibold mb-2">Telemetry Analysis</div>
              <p className="text-sm text-gray-400">
                Deep dive into throttle, brake, and steering inputs frame by frame.
              </p>
            </div>
            <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
              <div className="text-blue-400 font-semibold mb-2">Lap Comparison</div>
              <p className="text-sm text-gray-400">
                Compare your laps side-by-side to find where you're losing time.
              </p>
            </div>
            <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
              <div className="text-blue-400 font-semibold mb-2">Corner Analysis</div>
              <p className="text-sm text-gray-400">
                Identify braking points and apex speeds for every corner.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-gray-500 text-sm border-t border-gray-800/50">
        LapEvo - Evolve your driving.
      </footer>
    </div>
  );
}
