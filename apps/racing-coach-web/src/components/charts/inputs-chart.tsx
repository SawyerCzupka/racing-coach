import { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { TelemetryFrame } from '@/lib/types';

interface InputsChartProps {
  telemetry: TelemetryFrame[];
  height?: number;
}

export function InputsChart({ telemetry, height = 300 }: InputsChartProps) {
  const data = useMemo(() => {
    const distances = telemetry.map((f) => f.lap_distance);
    const throttle = telemetry.map((f) => f.throttle * 100);
    const brake = telemetry.map((f) => f.brake * 100);

    return [
      {
        x: distances,
        y: throttle,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Throttle',
        line: {
          color: '#22c55e',
          width: 2,
        },
        hovertemplate: '%{y:.1f}%<extra></extra>',
      },
      {
        x: distances,
        y: brake,
        type: 'scatter' as const,
        mode: 'lines' as const,
        name: 'Brake',
        line: {
          color: '#ef4444',
          width: 2,
        },
        hovertemplate: '%{y:.1f}%<extra></extra>',
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
        title: { text: 'Input (%)' },
        gridcolor: '#374151',
        zerolinecolor: '#4b5563',
        range: [0, 105],
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
