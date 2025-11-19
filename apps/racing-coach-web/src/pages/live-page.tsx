export function LivePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Live Session</h2>
        <p className="text-gray-400">
          Real-time telemetry and lap monitoring
        </p>
      </div>

      <div className="flex items-center justify-center rounded-lg border border-gray-800 bg-gray-900 p-8">
        <div className="text-center space-y-2">
          <div className="inline-block h-4 w-4 rounded-full bg-gray-600 animate-pulse" />
          <p className="text-gray-400">
            Waiting for active session...
          </p>
        </div>
      </div>
    </div>
  );
}
