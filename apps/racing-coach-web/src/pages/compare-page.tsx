import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LoadingState, EmptyState } from '@/components/ui/loading-states';
import { formatLapTime, formatDelta, getDeltaColor } from '@/lib/format';
import { useCompareLapsApiV1MetricsCompareGet } from '@/api/generated/metrics/metrics';
import { useGetSessionsList, useGetSessionDetail } from '@/api/generated/sessions/sessions';
import type {
  BrakingZoneComparison,
  CornerComparison,
  SessionSummary,
  LapSummary,
} from '@/api/generated/models';

export function ComparePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

  const lap1 = searchParams.get('lap1') ?? '';
  const lap2 = searchParams.get('lap2') ?? '';

  // Fetch sessions for selection
  const { data: sessionsResponse, isLoading: sessionsLoading } = useGetSessionsList();
  const sessions: SessionSummary[] = sessionsResponse?.sessions ?? [];

  // Fetch selected session details to get laps
  const { data: sessionResponse } = useGetSessionDetail(
    selectedSession ?? '',
    { query: { enabled: !!selectedSession } }
  );
  const sessionLaps: LapSummary[] = sessionResponse?.laps ?? [];

  // Fetch comparison data when both laps are selected
  const { data: comparison, isLoading: comparisonLoading, error: comparisonError } =
    useCompareLapsApiV1MetricsCompareGet(
      { lap_id_1: lap1, lap_id_2: lap2 },
      { query: { enabled: !!lap1 && !!lap2 } }
    );

  const handleLapSelect = (lapNum: 1 | 2, lapId: string) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set(`lap${lapNum}`, lapId);
    setSearchParams(newParams);
  };

  // If no laps selected, show the selection UI
  if (!lap1 || !lap2) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Compare Laps</h2>
          <p className="text-gray-400">Select two laps to compare their performance</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Baseline Lap Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Baseline Lap</CardTitle>
              <CardDescription>Select the reference lap for comparison</CardDescription>
            </CardHeader>
            <CardContent>
              {lap1 ? (
                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
                  <p className="text-white font-medium">Lap Selected</p>
                  <p className="text-sm text-gray-400">{lap1}</p>
                  <button
                    onClick={() => handleLapSelect(1, '')}
                    className="mt-2 text-sm text-blue-400 hover:text-blue-300"
                  >
                    Change selection
                  </button>
                </div>
              ) : (
                <LapSelector
                  sessions={sessions}
                  sessionsLoading={sessionsLoading}
                  selectedSession={selectedSession}
                  onSessionSelect={setSelectedSession}
                  sessionLaps={sessionLaps}
                  onLapSelect={(lapId) => handleLapSelect(1, lapId)}
                />
              )}
            </CardContent>
          </Card>

          {/* Comparison Lap Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Comparison Lap</CardTitle>
              <CardDescription>Select the lap to compare against baseline</CardDescription>
            </CardHeader>
            <CardContent>
              {lap2 ? (
                <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/30">
                  <p className="text-white font-medium">Lap Selected</p>
                  <p className="text-sm text-gray-400">{lap2}</p>
                  <button
                    onClick={() => handleLapSelect(2, '')}
                    className="mt-2 text-sm text-green-400 hover:text-green-300"
                  >
                    Change selection
                  </button>
                </div>
              ) : (
                <LapSelector
                  sessions={sessions}
                  sessionsLoading={sessionsLoading}
                  selectedSession={selectedSession}
                  onSessionSelect={setSelectedSession}
                  sessionLaps={sessionLaps}
                  onLapSelect={(lapId) => handleLapSelect(2, lapId)}
                />
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Show comparison results
  if (comparisonLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Compare Laps</h2>
          <p className="text-gray-400">Loading comparison data...</p>
        </div>
        <Card>
          <LoadingState message="Comparing laps..." />
        </Card>
      </div>
    );
  }

  if (comparisonError || !comparison) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Compare Laps</h2>
          <p className="text-gray-400">Unable to compare laps</p>
        </div>
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <p className="text-gray-400 mb-4">
                Could not compare these laps. Make sure both laps have metrics computed.
              </p>
              <button
                onClick={() => {
                  setSearchParams(new URLSearchParams());
                }}
                className="text-blue-400 hover:text-blue-300"
              >
                Select different laps
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const summary = comparison.summary;
  const brakingComparisons = comparison.braking_zone_comparisons ?? [];
  const cornerComparisons = comparison.corner_comparisons ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight text-white">Lap Comparison</h2>
          <p className="text-gray-400">
            Baseline vs Comparison lap analysis
          </p>
        </div>
        <button
          onClick={() => setSearchParams(new URLSearchParams())}
          className="text-sm text-gray-400 hover:text-white"
        >
          Compare different laps
        </button>
      </div>

      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
          <CardDescription>Overall lap time and performance deltas</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Lap Time Comparison */}
            <div className="text-center p-4 rounded-lg bg-gray-800/50">
              <p className="text-sm text-gray-400 mb-2">Lap Time Delta</p>
              <p className={`text-3xl font-bold ${getDeltaColor(summary.lap_time_delta ?? 0)}`}>
                {summary.lap_time_delta != null ? formatDelta(summary.lap_time_delta) : 'N/A'}
              </p>
              <div className="mt-2 text-sm">
                <span className="text-blue-400">
                  {summary.baseline_lap_time ? formatLapTime(summary.baseline_lap_time) : '--:--.---'}
                </span>
                <span className="text-gray-500 mx-2">vs</span>
                <span className="text-green-400">
                  {summary.comparison_lap_time ? formatLapTime(summary.comparison_lap_time) : '--:--.---'}
                </span>
              </div>
            </div>

            {/* Max Speed Delta */}
            <div className="text-center p-4 rounded-lg bg-gray-800/50">
              <p className="text-sm text-gray-400 mb-2">Max Speed Delta</p>
              <p className={`text-3xl font-bold ${getDeltaColor(-(summary.max_speed_delta ?? 0))}`}>
                {summary.max_speed_delta != null ? `${(summary.max_speed_delta * 3.6).toFixed(1)} km/h` : 'N/A'}
              </p>
            </div>

            {/* Corner Speed Delta */}
            <div className="text-center p-4 rounded-lg bg-gray-800/50">
              <p className="text-sm text-gray-400 mb-2">Avg Corner Speed Delta</p>
              <p className={`text-3xl font-bold ${getDeltaColor(-(summary.average_corner_speed_delta ?? 0))}`}>
                {summary.average_corner_speed_delta != null
                  ? `${(summary.average_corner_speed_delta * 3.6).toFixed(1)} km/h`
                  : 'N/A'}
              </p>
            </div>
          </div>

          <div className="mt-4 flex justify-center gap-8 text-sm text-gray-400">
            <span>
              Braking Zones: {summary.matched_braking_zones}/{summary.total_braking_zones_baseline} matched
            </span>
            <span>
              Corners: {summary.matched_corners}/{summary.total_corners_baseline} matched
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Braking Zone Comparisons */}
      {brakingComparisons.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Braking Zone Comparisons</CardTitle>
            <CardDescription>Zone-by-zone braking performance deltas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {brakingComparisons.map((zone: BrakingZoneComparison, index: number) => (
                <div
                  key={index}
                  className="p-4 rounded-lg bg-gray-800/50 border border-gray-700"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-lg font-semibold text-white">Zone {zone.zone_index + 1}</span>
                    {zone.matched_zone_index != null ? (
                      <Badge variant="success" className="text-xs">Matched</Badge>
                    ) : (
                      <Badge variant="default" className="text-xs">Unmatched</Badge>
                    )}
                  </div>
                  {zone.matched_zone_index != null ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Entry Speed</span>
                        <span className={getDeltaColor(-(zone.braking_point_speed_delta ?? 0))}>
                          {zone.braking_point_speed_delta != null
                            ? `${(zone.braking_point_speed_delta * 3.6).toFixed(1)} km/h`
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Min Speed</span>
                        <span className={getDeltaColor(-(zone.minimum_speed_delta ?? 0))}>
                          {zone.minimum_speed_delta != null
                            ? `${(zone.minimum_speed_delta * 3.6).toFixed(1)} km/h`
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Duration</span>
                        <span className={getDeltaColor(zone.braking_duration_delta ?? 0)}>
                          {zone.braking_duration_delta != null
                            ? formatDelta(zone.braking_duration_delta)
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Efficiency</span>
                        <span className={getDeltaColor(-(zone.braking_efficiency_delta ?? 0))}>
                          {zone.braking_efficiency_delta != null
                            ? `${(zone.braking_efficiency_delta * 100).toFixed(1)}%`
                            : '--'}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No matching zone in comparison lap</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Corner Comparisons */}
      {cornerComparisons.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Corner Comparisons</CardTitle>
            <CardDescription>Corner-by-corner performance deltas</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {cornerComparisons.map((corner: CornerComparison, index: number) => (
                <div
                  key={index}
                  className="p-4 rounded-lg bg-gray-800/50 border border-gray-700"
                >
                  <div className="flex justify-between items-center mb-3">
                    <span className="text-lg font-semibold text-white">Corner {corner.corner_index + 1}</span>
                    {corner.matched_corner_index != null ? (
                      <Badge variant="success" className="text-xs">Matched</Badge>
                    ) : (
                      <Badge variant="default" className="text-xs">Unmatched</Badge>
                    )}
                  </div>
                  {corner.matched_corner_index != null ? (
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Entry Speed</span>
                        <span className={getDeltaColor(-(corner.turn_in_speed_delta ?? 0))}>
                          {corner.turn_in_speed_delta != null
                            ? `${(corner.turn_in_speed_delta * 3.6).toFixed(1)} km/h`
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Apex Speed</span>
                        <span className={getDeltaColor(-(corner.apex_speed_delta ?? 0))}>
                          {corner.apex_speed_delta != null
                            ? `${(corner.apex_speed_delta * 3.6).toFixed(1)} km/h`
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Exit Speed</span>
                        <span className={getDeltaColor(-(corner.exit_speed_delta ?? 0))}>
                          {corner.exit_speed_delta != null
                            ? `${(corner.exit_speed_delta * 3.6).toFixed(1)} km/h`
                            : '--'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Time in Corner</span>
                        <span className={getDeltaColor(corner.time_in_corner_delta ?? 0)}>
                          {corner.time_in_corner_delta != null
                            ? formatDelta(corner.time_in_corner_delta)
                            : '--'}
                        </span>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">No matching corner in comparison lap</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Lap selector component
interface LapSelectorProps {
  sessions: SessionSummary[];
  sessionsLoading: boolean;
  selectedSession: string | null;
  onSessionSelect: (sessionId: string) => void;
  sessionLaps: LapSummary[];
  onLapSelect: (lapId: string) => void;
}

function LapSelector({
  sessions,
  sessionsLoading,
  selectedSession,
  onSessionSelect,
  sessionLaps,
  onLapSelect,
}: LapSelectorProps) {
  if (sessionsLoading) {
    return <LoadingState message="Loading sessions..." />;
  }

  if (sessions.length === 0) {
    return <EmptyState message="No sessions available" />;
  }

  return (
    <div className="space-y-4">
      {/* Session Selector */}
      <div>
        <label className="block text-sm text-gray-400 mb-2">Select Session</label>
        <select
          value={selectedSession ?? ''}
          onChange={(e) => onSessionSelect(e.target.value)}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Choose a session...</option>
          {sessions.map((session) => (
            <option key={session.session_id} value={session.session_id}>
              {session.track_name} - {session.car_name}
            </option>
          ))}
        </select>
      </div>

      {/* Lap Selector */}
      {selectedSession && sessionLaps.length > 0 && (
        <div>
          <label className="block text-sm text-gray-400 mb-2">Select Lap</label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {sessionLaps.filter(lap => lap.has_metrics).map((lap) => (
              <button
                key={lap.lap_id}
                onClick={() => onLapSelect(lap.lap_id)}
                className="w-full p-3 text-left rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-gray-600 transition-colors"
              >
                <div className="flex justify-between items-center">
                  <span className="text-white font-medium">Lap {lap.lap_number}</span>
                  <span className="text-gray-400 font-mono">
                    {lap.lap_time ? formatLapTime(lap.lap_time) : '--:--.---'}
                  </span>
                </div>
              </button>
            ))}
          </div>
          {sessionLaps.filter(lap => lap.has_metrics).length === 0 && (
            <p className="text-sm text-gray-500">No laps with computed metrics in this session</p>
          )}
        </div>
      )}

      {selectedSession && sessionLaps.length === 0 && (
        <p className="text-sm text-gray-500">No laps recorded in this session</p>
      )}
    </div>
  );
}
