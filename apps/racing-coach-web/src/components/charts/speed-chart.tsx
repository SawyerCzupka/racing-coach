import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { TelemetryFrame } from '@/lib/types';

interface SpeedChartProps {
  telemetry: TelemetryFrame[];
  height?: number;
}

export function SpeedChart({ telemetry, height = 400 }: SpeedChartProps) {
  const data = useMemo(() => {
    const distances = telemetry.map((f) => f.lap_distance);
    const speeds = telemetry.map((f) => f.speed * 3.6); // Convert m/s to km/h

    return [
      {
        x: distances,
        y: speeds,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Speed',
        line: {
          color: '#60a5fa',
          width: 2,
        },
        hovertemplate: '%{y:.1f} km/h<extra></extra>',
      },
    ];
  }, [telemetry]);

  const layout = useMemo(
    () => ({
      height,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(17, 24, 39, 0.5)',
      font: {
        color: '#e5e7eb',
        family: 'system-ui, -apple-system, sans-serif',
      },
      margin: { l: 60, r: 40, t: 40, b: 60 },
      xaxis: {
        title: { text: 'Distance (m)' },
        gridcolor: '#374151',
        zerolinecolor: '#4b5563',
      },
      yaxis: {
        title: { text: 'Speed (km/h)' },
        gridcolor: '#374151',
        zerolinecolor: '#4b5563',
      },
      hovermode: 'x unified' as const,
    }),
    [height]
  );

  const config = useMemo(
    () => ({
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
    }),
    []
  );

  return <Plot data={data as any} layout={layout as any} config={config} className="w-full" />;
}
