import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { TelemetryFrame } from '@/lib/types';

interface GForceChartProps {
  telemetry: TelemetryFrame[];
  height?: number;
}

export function GForceChart({ telemetry, height = 300 }: GForceChartProps) {
  const data = useMemo(() => {
    const distances = telemetry.map((f) => f.lap_distance);
    const lateralG = telemetry.map((f) => f.lateral_acceleration / 9.81); // Convert to G
    const longitudinalG = telemetry.map((f) => f.longitudinal_acceleration / 9.81);

    return [
      {
        x: distances,
        y: lateralG,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Lateral G',
        line: {
          color: '#a78bfa',
          width: 2,
        },
        hovertemplate: '%{y:.2f}G<extra></extra>',
      },
      {
        x: distances,
        y: longitudinalG,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Longitudinal G',
        line: {
          color: '#fb923c',
          width: 2,
        },
        hovertemplate: '%{y:.2f}G<extra></extra>',
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
        title: { text: 'G-Force' },
        gridcolor: '#374151',
        zerolinecolor: '#4b5563',
      },
      hovermode: 'x unified' as const,
      legend: {
        x: 1,
        xanchor: 'right' as const,
        y: 1,
      },
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
