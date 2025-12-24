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
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/format';
import { useGetSessionsList } from '@/api/generated/sessions/sessions';
import { useAuth } from '@/providers/auth-provider';

export function DashboardPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { data: response, isLoading, error } = useGetSessionsList();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Dashboard</h2>
          <p className="text-gray-400">Loading your racing data...</p>
        </div>
        <Card>
          <LoadingState message="Loading dashboard..." />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Dashboard</h2>
        </div>
        <Card>
          <ErrorState error={error instanceof Error ? error : new Error('Failed to load dashboard')} />
        </Card>
      </div>
    );
  }

  const sessions = response?.sessions ?? [];
  const recentSessions = sessions.slice(0, 5);
  const totalSessions = response?.total ?? sessions.length;
  const totalLaps = sessions.reduce((acc, s) => acc + s.lap_count, 0);
  const uniqueTracks = new Set(sessions.map((s) => s.track_name)).size;
  const uniqueCars = new Set(sessions.map((s) => s.car_name)).size;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Welcome back{user?.display_name ? `, ${user.display_name}` : ''}
          </h2>
          <p className="text-gray-400">Here's your racing overview</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/compare')}>
            Compare Laps
          </Button>
          <Button onClick={() => navigate('/live')}>Live Session</Button>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Total Sessions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{totalSessions}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Total Laps</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{totalLaps}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Tracks Driven</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{uniqueTracks}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Cars Used</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{uniqueCars}</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Sessions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Recent Sessions</CardTitle>
            <CardDescription>Your last 5 racing sessions</CardDescription>
          </div>
          <Button variant="ghost" onClick={() => navigate('/sessions')}>
            View All
          </Button>
        </CardHeader>
        <CardContent>
          {recentSessions.length === 0 ? (
            <EmptyState message="No sessions yet. Start racing to see your data here!" />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Track</TableHead>
                  <TableHead>Car</TableHead>
                  <TableHead>Laps</TableHead>
                  <TableHead>When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentSessions.map((session) => (
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
                    <TableCell className="text-white">{session.car_name}</TableCell>
                    <TableCell>
                      <Badge variant="default">{session.lap_count}</Badge>
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-gray-400">
                        {formatRelativeTime(session.created_at)}
                      </span>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
