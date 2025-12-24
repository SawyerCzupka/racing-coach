import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Breadcrumbs } from '@/components/ui/breadcrumbs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { LoadingState, EmptyState, ErrorState } from '@/components/ui/loading-states';
import { formatDateTime, formatLapTime } from '@/lib/format';
import { useGetSessionDetail } from '@/api/generated/sessions/sessions';
import type { LapSummary } from '@/api/generated/models';

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { data: response, isLoading, error } = useGetSessionDetail(
    sessionId || ""
  );

  // Check if response is successful (status 200)
  // const session: SessionDetailResponse | undefined =
  //   response?.status === 200 ? response.data : undefined;

  const session = response

  console.log(response)
  console.log(session)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Session Details</h2>
          <p className="text-gray-400">Loading session information...</p>
        </div>
        <Card>
          <LoadingState message="Loading session..." />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Session Details</h2>
          <p className="text-gray-400">Error loading session</p>
        </div>
        <Card>
          <ErrorState error={error instanceof Error ? error : new Error('Failed to load session')} />
        </Card>
      </div>
    );
  }

  if (!session) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Session Details</h2>
          <p className="text-gray-400">Session not found</p>
        </div>
        <Card>
          <EmptyState message="Session not found" />
        </Card>
      </div>
    );
  }

  const laps = session.laps ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Breadcrumbs
            items={[
              { label: 'Dashboard', href: '/dashboard' },
              { label: 'Sessions', href: '/sessions' },
              { label: session.track_name },
            ]}
            className="mb-3"
          />
          <h2 className="text-3xl font-bold tracking-tight text-white">
            {session.track_name}
          </h2>
          {session.track_config_name && (
            <p className="text-xl text-gray-400">{session.track_config_name}</p>
          )}
        </div>
        <Badge variant="info">{laps.length} Laps</Badge>
      </div>

      {/* Session Info */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Car</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold text-white">{session.car_name}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Track Type</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold text-white capitalize">{session.track_type}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Date</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xl font-semibold text-white">{formatDateTime(session.created_at)}</p>
          </CardContent>
        </Card>
      </div>

      {/* Laps Table */}
      <Card>
        <CardHeader>
          <CardTitle>Laps</CardTitle>
          <CardDescription>Click on a lap to view detailed telemetry</CardDescription>
        </CardHeader>
        <CardContent>
          {laps.length === 0 ? (
            <EmptyState message="No laps recorded in this session" />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Lap</TableHead>
                    <TableHead>Time</TableHead>
                    <TableHead>Valid</TableHead>
                    <TableHead>Metrics</TableHead>
                    <TableHead>Recorded</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {laps.map((lap: LapSummary) => (
                    <TableRow
                      key={lap.lap_id}
                      onClick={() => navigate(`/lap/${lap.lap_id}`)}
                    >
                      <TableCell>
                        <span className="font-medium text-white">Lap {lap.lap_number}</span>
                      </TableCell>
                      <TableCell>
                        <span className="font-mono text-white">
                          {lap.lap_time ? formatLapTime(lap.lap_time) : '--:--.---'}
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge variant={lap.is_valid ? 'success' : 'danger'}>
                          {lap.is_valid ? 'Valid' : 'Invalid'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={lap.has_metrics ? 'info' : 'default'}>
                          {lap.has_metrics ? 'Analyzed' : 'Pending'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <span className="text-sm text-gray-400">
                          {formatDateTime(lap.created_at)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
