/**
 * Utility functions for track coordinate conversions.
 *
 * Converts between lap distance (meters) and GPS coordinates using track boundary data.
 */

import type { TrackBoundaryResponse } from '@/api/generated/models';

/**
 * GPS coordinate point.
 */
export interface GpsPoint {
  latitude: number;
  longitude: number;
}

/**
 * Convert a lap distance in meters to GPS coordinates on the centerline.
 *
 * @param distance - Distance in meters from start/finish line
 * @param boundary - Track boundary data
 * @returns GPS coordinates on the track centerline
 */
export function distanceToGps(distance: number, boundary: TrackBoundaryResponse): GpsPoint {
  const trackLength = boundary.track_length ?? 0;
  if (trackLength <= 0) {
    throw new Error('Track length is not available');
  }

  // Convert distance to percentage (0.0-1.0)
  let distancePct = distance / trackLength;

  // Handle wrap-around and negative distances
  distancePct = ((distancePct % 1.0) + 1.0) % 1.0;

  // Find grid index
  const gridSpacing = 1.0 / boundary.grid_size;
  const idxFloat = distancePct / gridSpacing;
  const idxLow = Math.floor(idxFloat) % boundary.grid_size;
  const idxHigh = (idxLow + 1) % boundary.grid_size;
  const t = idxFloat - Math.floor(idxFloat);

  // Interpolate boundary positions
  const leftLat = (1 - t) * boundary.left_latitude[idxLow] + t * boundary.left_latitude[idxHigh];
  const leftLon = (1 - t) * boundary.left_longitude[idxLow] + t * boundary.left_longitude[idxHigh];
  const rightLat =
    (1 - t) * boundary.right_latitude[idxLow] + t * boundary.right_latitude[idxHigh];
  const rightLon =
    (1 - t) * boundary.right_longitude[idxLow] + t * boundary.right_longitude[idxHigh];

  // Return centerline position
  return {
    latitude: (leftLat + rightLat) / 2,
    longitude: (leftLon + rightLon) / 2,
  };
}

/**
 * Project a point onto a line segment, returning parameter t in [0,1].
 * t=0 means the projection is at segStart, t=1 means at segEnd.
 */
function projectPointOntoSegment(
  point: GpsPoint,
  segStart: GpsPoint,
  segEnd: GpsPoint
): number {
  const dx = segEnd.longitude - segStart.longitude;
  const dy = segEnd.latitude - segStart.latitude;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return 0;

  const t =
    ((point.longitude - segStart.longitude) * dx +
      (point.latitude - segStart.latitude) * dy) /
    lenSq;

  return Math.max(0, Math.min(1, t));
}

/**
 * Convert GPS coordinates to precise lap distance in meters.
 *
 * Uses linear interpolation between grid points for sub-grid precision.
 * Finds the nearest point on the track centerline and returns its distance.
 *
 * @param point - GPS coordinates to convert
 * @param boundary - Track boundary data
 * @returns Distance in meters from start/finish line
 */
export function gpsToDistance(point: GpsPoint, boundary: TrackBoundaryResponse): number {
  const trackLength = boundary.track_length ?? 0;
  if (trackLength <= 0) {
    throw new Error('Track length is not available');
  }

  // Calculate centerline coordinates
  const centerLat = boundary.left_latitude.map(
    (lat: number, i: number) => (lat + boundary.right_latitude[i]) / 2
  );
  const centerLon = boundary.left_longitude.map(
    (lon: number, i: number) => (lon + boundary.right_longitude[i]) / 2
  );

  // Find nearest grid point by checking all points
  let minDistSq = Infinity;
  let nearestIdx = 0;

  for (let i = 0; i < boundary.grid_size; i++) {
    const dLat = point.latitude - centerLat[i];
    const dLon = point.longitude - centerLon[i];
    const distSq = dLat * dLat + dLon * dLon;

    if (distSq < minDistSq) {
      minDistSq = distSq;
      nearestIdx = i;
    }
  }

  // Interpolate between nearest and adjacent grid points for sub-grid precision
  const gridSpacing = trackLength / boundary.grid_size;
  const baseDistance = nearestIdx * gridSpacing;

  // Check previous and next segments
  const prevIdx = (nearestIdx - 1 + boundary.grid_size) % boundary.grid_size;
  const nextIdx = (nearestIdx + 1) % boundary.grid_size;

  // Project click point onto segment from prev to nearest
  const tPrev = projectPointOntoSegment(
    point,
    { latitude: centerLat[prevIdx], longitude: centerLon[prevIdx] },
    { latitude: centerLat[nearestIdx], longitude: centerLon[nearestIdx] }
  );

  // Project onto segment from nearest to next
  const tNext = projectPointOntoSegment(
    point,
    { latitude: centerLat[nearestIdx], longitude: centerLon[nearestIdx] },
    { latitude: centerLat[nextIdx], longitude: centerLon[nextIdx] }
  );

  // Use the projection that gives a value in valid range
  // tPrev in (0, 1) means point is between prev and nearest
  if (tPrev > 0 && tPrev < 1) {
    // Point is between prev and nearest, so distance is less than baseDistance
    return Math.max(0, baseDistance - (1 - tPrev) * gridSpacing);
  } else if (tNext > 0 && tNext < 1) {
    // Point is between nearest and next, so distance is greater than baseDistance
    return Math.min(trackLength, baseDistance + tNext * gridSpacing);
  }

  // Fallback to base distance if projections don't apply
  return baseDistance;
}

/**
 * Get GPS coordinates for left and right boundary at a given distance.
 *
 * @param distance - Distance in meters from start/finish line
 * @param boundary - Track boundary data
 * @returns Left and right boundary GPS coordinates
 */
export function distanceToBoundaryPoints(
  distance: number,
  boundary: TrackBoundaryResponse
): { left: GpsPoint; right: GpsPoint } {
  const trackLength = boundary.track_length ?? 0;
  if (trackLength <= 0) {
    throw new Error('Track length is not available');
  }

  // Convert distance to percentage (0.0-1.0)
  let distancePct = distance / trackLength;
  distancePct = ((distancePct % 1.0) + 1.0) % 1.0;

  // Find grid index
  const gridSpacing = 1.0 / boundary.grid_size;
  const idxFloat = distancePct / gridSpacing;
  const idxLow = Math.floor(idxFloat) % boundary.grid_size;
  const idxHigh = (idxLow + 1) % boundary.grid_size;
  const t = idxFloat - Math.floor(idxFloat);

  return {
    left: {
      latitude: (1 - t) * boundary.left_latitude[idxLow] + t * boundary.left_latitude[idxHigh],
      longitude: (1 - t) * boundary.left_longitude[idxLow] + t * boundary.left_longitude[idxHigh],
    },
    right: {
      latitude: (1 - t) * boundary.right_latitude[idxLow] + t * boundary.right_latitude[idxHigh],
      longitude: (1 - t) * boundary.right_longitude[idxLow] + t * boundary.right_longitude[idxHigh],
    },
  };
}

/**
 * Generate a series of GPS points along the centerline between two distances.
 * Useful for drawing corner regions on the map.
 *
 * @param startDistance - Start distance in meters
 * @param endDistance - End distance in meters
 * @param boundary - Track boundary data
 * @param numPoints - Number of points to generate (default: 20)
 * @returns Array of GPS points along the centerline
 */
export function generateCenterlineSegment(
  startDistance: number,
  endDistance: number,
  boundary: TrackBoundaryResponse,
  numPoints: number = 20
): GpsPoint[] {
  const points: GpsPoint[] = [];
  const step = (endDistance - startDistance) / (numPoints - 1);

  for (let i = 0; i < numPoints; i++) {
    const distance = startDistance + i * step;
    points.push(distanceToGps(distance, boundary));
  }

  return points;
}

/**
 * Generate polygon coordinates for a corner region (for shaded display).
 *
 * Creates a polygon that spans from left to right boundary between two distances.
 *
 * @param startDistance - Start distance in meters
 * @param endDistance - End distance in meters
 * @param boundary - Track boundary data
 * @param numPoints - Number of points per side (default: 10)
 * @returns Arrays of latitude and longitude for the polygon
 */
export function generateCornerPolygon(
  startDistance: number,
  endDistance: number,
  boundary: TrackBoundaryResponse,
  numPoints: number = 10
): { latitudes: number[]; longitudes: number[] } {
  const step = (endDistance - startDistance) / (numPoints - 1);
  const leftPoints: GpsPoint[] = [];
  const rightPoints: GpsPoint[] = [];

  // Generate points along both boundaries
  for (let i = 0; i < numPoints; i++) {
    const distance = startDistance + i * step;
    const { left, right } = distanceToBoundaryPoints(distance, boundary);
    leftPoints.push(left);
    rightPoints.push(right);
  }

  // Create closed polygon: left boundary forward, right boundary backward
  const latitudes: number[] = [];
  const longitudes: number[] = [];

  // Left boundary (start to end)
  for (const point of leftPoints) {
    latitudes.push(point.latitude);
    longitudes.push(point.longitude);
  }

  // Right boundary (end to start, reversed)
  for (let i = rightPoints.length - 1; i >= 0; i--) {
    latitudes.push(rightPoints[i].latitude);
    longitudes.push(rightPoints[i].longitude);
  }

  // Close the polygon
  latitudes.push(leftPoints[0].latitude);
  longitudes.push(leftPoints[0].longitude);

  return { latitudes, longitudes };
}
