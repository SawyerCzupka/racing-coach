import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingState, EmptyState, ErrorState } from '@/components/ui/loading-states';
import { formatDateTime } from '@/lib/format';

// Placeholder - will be replaced with real API hooks from Orval
function useSessions() {
  // Mock data for demonstration
  const mockSessions = [
    {
      session_id: '550e8400-e29b-41d4-a716-446655440001',
      track_name: 'Watkins Glen International',
      track_config_name: 'Boot',
      track_type: 'road',
      car_name: 'Porsche 911 GT3 Cup',
      series_id: 123,
      created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
      lap_count: 12,
    },
    {
      session_id: '550e8400-e29b-41d4-a716-446655440002',
      track_name: 'Brands Hatch Circuit',
      track_config_name: 'Grand Prix',
      track_type: 'road',
      car_name: 'BMW M4 GT3',
      series_id: 124,
      created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
      lap_count: 18,
    },
  ];

  return {
    data: mockSessions,
    isLoading: false,
    error: null,
  };
}

export function SessionsPage() {
  const navigate = useNavigate();
  const { data: sessions, isLoading, error } = useSessions();
  const [filter, setFilter] = useState('');

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Sessions</h2>
          <p className="text-gray-400">View and analyze your racing sessions</p>
        </div>
        <Card>
          <LoadingState message="Loading sessions..." />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Sessions</h2>
          <p className="text-gray-400">View and analyze your racing sessions</p>
        </div>
        <Card>
          <ErrorState error={error} />
        </Card>
      </div>
    );
  }

  if (!sessions || sessions.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Sessions</h2>
          <p className="text-gray-400">View and analyze your racing sessions</p>
        </div>
        <Card>
          <EmptyState message="No sessions found. Start racing to see your data here!" />
        </Card>
      </div>
    );
  }

  const filteredSessions = sessions.filter(
    (session) =>
      session.track_name.toLowerCase().includes(filter.toLowerCase()) ||
      session.car_name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Sessions</h2>
          <p className="text-gray-400">View and analyze your racing sessions</p>
        </div>
        <Badge variant="info">{sessions.length} Total Sessions</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Sessions</CardTitle>
          <CardDescription>Click on a session to view laps and telemetry</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <input
              type="text"
              placeholder="Filter by track or car..."
              className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
          </div>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Track</TableHead>
                  <TableHead>Car</TableHead>
                  <TableHead>Laps</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSessions.map((session) => (
                  <TableRow
                    key={session.session_id}
                    onClick={() => navigate(`/session/${session.session_id}`)}
                  >
                    <TableCell>
                      <div>
                        <div className="font-medium text-white">{session.track_name}</div>
                        {session.track_config_name && (
                          <div className="text-sm text-gray-400">{session.track_config_name}</div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="text-white">{session.car_name}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="default">{session.lap_count} laps</Badge>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm text-gray-400">
                        {formatDateTime(session.created_at)}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {filteredSessions.length === 0 && filter && (
            <div className="text-center py-8">
              <p className="text-gray-400">No sessions match your filter</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
