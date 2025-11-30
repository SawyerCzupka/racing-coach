//! Mathematical utility functions.

/// Handle lap distance wrap-around at start/finish line.
///
/// When calculating distance deltas, if the result is negative it means
/// we crossed the start/finish line (e.g., 0.99 -> 0.01 = -0.98).
/// This function corrects that to the actual distance traveled (0.02).
///
/// Assumes lap_distance is normalized to 0.0-1.0.
///
/// # Examples
/// ```
/// use racing_coach_core::utils::wrap_distance;
///
/// assert_eq!(wrap_distance(0.1), 0.1);    // Normal case
/// assert_eq!(wrap_distance(-0.98), 0.02); // Crossed S/F line
/// ```
#[inline]
pub fn wrap_distance(delta: f64) -> f64 {
    if delta < 0.0 {
        delta + 1.0
    } else {
        delta
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_wrap_distance_positive() {
        assert_eq!(wrap_distance(0.1), 0.1);
        assert_eq!(wrap_distance(0.5), 0.5);
        assert_eq!(wrap_distance(0.0), 0.0);
    }

    #[test]
    fn test_wrap_distance_negative() {
        let delta = wrap_distance(-0.98);
        assert!((delta - 0.02).abs() < 1e-10);

        let delta = wrap_distance(-0.5);
        assert!((delta - 0.5).abs() < 1e-10);
    }

    #[test]
    fn test_wrap_distance_exact_crossing() {
        // Going from 0.99 to 0.01
        let delta = 0.01 - 0.99;
        let wrapped = wrap_distance(delta);
        assert!((wrapped - 0.02).abs() < 1e-10);
    }
}
