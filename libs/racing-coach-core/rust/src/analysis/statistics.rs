//! Statistics accumulators for telemetry analysis.

/// Accumulator for tracking speed statistics during a single pass.
///
/// This struct efficiently tracks min, max, and sum of speeds
/// without requiring a separate pass through the data.
#[derive(Debug, Clone)]
pub struct SpeedStatistics {
    min: f64,
    max: f64,
    sum: f64,
    count: usize,
}

impl SpeedStatistics {
    /// Create a new empty statistics accumulator.
    pub fn new() -> Self {
        Self {
            min: f64::INFINITY,
            max: f64::NEG_INFINITY,
            sum: 0.0,
            count: 0,
        }
    }

    /// Update statistics with a new speed value.
    #[inline]
    pub fn update(&mut self, speed: f64) {
        self.min = self.min.min(speed);
        self.max = self.max.max(speed);
        self.sum += speed;
        self.count += 1;
    }

    /// Get the minimum speed observed.
    ///
    /// Returns 0.0 if no values have been added.
    pub fn min(&self) -> f64 {
        if self.count == 0 {
            0.0
        } else {
            self.min
        }
    }

    /// Get the maximum speed observed.
    ///
    /// Returns 0.0 if no values have been added.
    pub fn max(&self) -> f64 {
        if self.count == 0 {
            0.0
        } else {
            self.max
        }
    }

    /// Get the average speed.
    ///
    /// Returns 0.0 if no values have been added.
    pub fn mean(&self) -> f64 {
        if self.count == 0 {
            0.0
        } else {
            self.sum / self.count as f64
        }
    }

    /// Get the count of values added.
    pub fn count(&self) -> usize {
        self.count
    }
}

impl Default for SpeedStatistics {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_empty_statistics() {
        let stats = SpeedStatistics::new();
        assert_eq!(stats.min(), 0.0);
        assert_eq!(stats.max(), 0.0);
        assert_eq!(stats.mean(), 0.0);
        assert_eq!(stats.count(), 0);
    }

    #[test]
    fn test_single_value() {
        let mut stats = SpeedStatistics::new();
        stats.update(50.0);

        assert_eq!(stats.min(), 50.0);
        assert_eq!(stats.max(), 50.0);
        assert_eq!(stats.mean(), 50.0);
        assert_eq!(stats.count(), 1);
    }

    #[test]
    fn test_multiple_values() {
        let mut stats = SpeedStatistics::new();
        stats.update(30.0);
        stats.update(50.0);
        stats.update(100.0);
        stats.update(20.0);

        assert_eq!(stats.min(), 20.0);
        assert_eq!(stats.max(), 100.0);
        assert_eq!(stats.mean(), 50.0); // (30+50+100+20)/4 = 200/4 = 50
        assert_eq!(stats.count(), 4);
    }

    #[test]
    fn test_default() {
        let stats = SpeedStatistics::default();
        assert_eq!(stats.count(), 0);
    }
}
