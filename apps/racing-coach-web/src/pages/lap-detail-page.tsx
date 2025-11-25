import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LoadingState, EmptyState } from '@/components/ui/loading-states';
import { formatLapTime, formatSpeed, formatGForce, formatDistance } from '@/lib/format';
import { useGetLapMetricsApiV1MetricsLapLapIdGet } from '@/api/generated/metrics/metrics';
import type { BrakingMetrics, CornerMetrics } from '@/api/generated/models';

export function LapDetailPage() {
  const { lapId } = useParams<{ lapId: string }>();
  const navigate = useNavigate();
  const { data: metrics, isLoading, error } = useGetLapMetricsApiV1MetricsLapLapIdGet(
    lapId ?? ''
  );

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Lap Details</h2>
          <p className="text-gray-400">Loading lap information...</p>
        </div>
        <Card>
          <LoadingState message="Loading lap metrics..." />
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-white mb-2 flex items-center gap-1"
          >
            &larr; Back
          </button>
          <h2 className="text-3xl font-bold tracking-tight text-white">Lap Details</h2>
          <p className="text-gray-400">No metrics available for this lap</p>
        </div>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <p className="text-gray-400 mb-4">
                Metrics have not been computed for this lap yet.
              </p>
              <p className="text-sm text-gray-500">
                Lap metrics are calculated after telemetry data is uploaded and processed.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="space-y-6">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-white mb-2 flex items-center gap-1"
          >
            &larr; Back
          </button>
          <h2 className="text-3xl font-bold tracking-tight text-white">Lap Details</h2>
          <p className="text-gray-400">Lap not found</p>
        </div>
        <Card>
          <EmptyState message="Lap not found" />
        </Card>
      </div>
    );
  }

  const brakingZones = metrics.braking_zones ?? [];
  const corners = metrics.corners ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-gray-400 hover:text-white mb-2 flex items-center gap-1"
          >
            &larr; Back
          </button>
          <h2 className="text-3xl font-bold tracking-tight text-white">
            Lap Analysis
          </h2>
          <p className="text-xl text-gray-400">
            {metrics.lap_time ? formatLapTime(metrics.lap_time) : 'Time not recorded'}
          </p>
        </div>
        <Badge variant="info">
          {corners.length} Corners | {brakingZones.length} Braking Zones
        </Badge>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Max Speed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white">{formatSpeed(metrics.max_speed)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Min Speed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white">{formatSpeed(metrics.min_speed)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Avg Corner Speed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white">{formatSpeed(metrics.average_corner_speed)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-400">Lap Time</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-white font-mono">
              {metrics.lap_time ? formatLapTime(metrics.lap_time) : '--:--.---'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Braking Zones */}
      <Card>
        <CardHeader>
          <CardTitle>Braking Zones</CardTitle>
          <CardDescription>Analysis of each braking zone in the lap</CardDescription>
        </CardHeader>
        <CardContent>
          {brakingZones.length === 0 ? (
            <EmptyState message="No braking zones detected" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {brakingZones.map((zone: BrakingMetrics, index: number) => (
                <div
                  key={index}
                  className="p-4 rounded-lg bg-gray-800/50 border border-gray-700"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-lg font-semibold text-white">Zone {index + 1}</span>
                    {zone.has_trail_braking && (
                      <Badge variant="success" className="text-xs">Trail Braking</Badge>
                    )}
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry Speed</span>
                      <span className="text-white">{formatSpeed(zone.braking_point_speed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Min Speed</span>
                      <span className="text-white">{formatSpeed(zone.minimum_speed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Max Brake</span>
                      <span className="text-white">{(zone.max_brake_pressure * 100).toFixed(0)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Duration</span>
                      <span className="text-white">{zone.braking_duration.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Efficiency</span>
                      <span className="text-white">{(zone.braking_efficiency * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Distance</span>
                      <span className="text-white">{formatDistance(zone.braking_point_distance)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Corners */}
      <Card>
        <CardHeader>
          <CardTitle>Corner Analysis</CardTitle>
          <CardDescription>Performance metrics for each corner</CardDescription>
        </CardHeader>
        <CardContent>
          {corners.length === 0 ? (
            <EmptyState message="No corners detected" />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {corners.map((corner: CornerMetrics, index: number) => (
                <div
                  key={index}
                  className="p-4 rounded-lg bg-gray-800/50 border border-gray-700"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-lg font-semibold text-white">Corner {index + 1}</span>
                    <Badge variant="default" className="text-xs">
                      {formatGForce(corner.max_lateral_g)}
                    </Badge>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Entry Speed</span>
                      <span className="text-white">{formatSpeed(corner.turn_in_speed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Apex Speed</span>
                      <span className="text-white">{formatSpeed(corner.apex_speed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Exit Speed</span>
                      <span className="text-white">{formatSpeed(corner.exit_speed)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Time in Corner</span>
                      <span className="text-white">{corner.time_in_corner.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Speed Lost</span>
                      <span className="text-red-400">{formatSpeed(corner.speed_loss)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Speed Gained</span>
                      <span className="text-green-400">{formatSpeed(corner.speed_gain)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
