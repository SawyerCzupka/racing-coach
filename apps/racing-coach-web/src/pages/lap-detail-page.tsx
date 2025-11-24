import { useParams } from 'react-router-dom';

export function LapDetailPage() {
  const { lapId } = useParams<{ lapId: string }>();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">Lap {lapId}</h2>
        <p className="text-gray-400">
          Telemetry analysis and performance metrics
        </p>
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
        <p className="text-gray-400">
          Telemetry charts will appear here
        </p>
      </div>
    </div>
  );
}
