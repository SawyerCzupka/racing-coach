import { useParams } from 'react-router-dom';

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight text-white">
          Session {sessionId}
        </h2>
        <p className="text-gray-400">Session details and laps</p>
      </div>

      <div className="rounded-lg border border-gray-800 bg-gray-900 p-8 text-center">
        <p className="text-gray-400">
          Session details and lap list will appear here
        </p>
      </div>
    </div>
  );
}
