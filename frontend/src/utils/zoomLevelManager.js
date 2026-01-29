import { VISUALIZATION } from '../constants/visualization';

// Percentage-based thresholds (0-1 range)
// These represent positions within the dynamic zoom range
export const ZOOM_THRESHOLD_PERCENTAGES = {
  DETAIL_VISIBLE: 0.25,   // 25% through zoom range - reveal eras
  HIGH_DETAIL: 0.50,      // 50% through zoom range - gradients, annual grid
  GRID_DENSITY: 0.75,     // 75% through zoom range - dotted grid
  // RULER_DETAIL is now calculated based on physical space constraints
};

/**
 * Calculate actual scale thresholds based on dynamic zoom bounds
 * @param {number} minScale - Minimum zoom scale (from computeMinScale)
 * @param {number} maxScale - Maximum zoom scale (from computeMaxScale)
 * @param {number} [layoutPixelsPerYear] - Actual base pixels per year from layout (optional)
 * @returns {Object} Calculated threshold scale values
 */
export function calculateThresholds(minScale, maxScale, layoutPixelsPerYear = null) {
  const range = maxScale - minScale;

  // Safety check: if range is too small, use fallback values
  if (range <= 0 || !isFinite(range)) {
    console.warn('Invalid zoom range for threshold calculation:', { minScale, maxScale });
    return {
      DETAIL_VISIBLE: 0.8,
      HIGH_DETAIL: 1.2,
      GRID_DENSITY: 1.5,
      RULER_DETAIL: 1.8
    };
  }

  // Calculate thresholds based on "Years Visible" (Inverse Linear Interpolation)
  // This matches user intuition: 50% threshold = 50% of the years range visible
  // Formula: harmonic mean interpolation
  const interpolateInverse = (min, max, percent) => {
    return (min * max) / ((1 - percent) * max + percent * min);
  };

  // Physical Space Calculation for Labels
  // We need enough pixels per year to fit "1999" (approx 30px) + gap (10px) = 40px
  // User screenshots showed overlap at 40px, so bumping to 60px for safety.
  const MIN_PIXELS_FOR_LABEL = 60;

  // Use actual layout PPI if available, otherwise fallback to standard Year Width
  const basePpy = layoutPixelsPerYear || VISUALIZATION.YEAR_WIDTH;
  const rulerDetailScale = MIN_PIXELS_FOR_LABEL / basePpy;

  const percentageBased = {
    DETAIL_VISIBLE: interpolateInverse(minScale, maxScale, ZOOM_THRESHOLD_PERCENTAGES.DETAIL_VISIBLE),
    HIGH_DETAIL: interpolateInverse(minScale, maxScale, ZOOM_THRESHOLD_PERCENTAGES.HIGH_DETAIL),
    GRID_DENSITY: interpolateInverse(minScale, maxScale, ZOOM_THRESHOLD_PERCENTAGES.GRID_DENSITY),
    RULER_DETAIL: rulerDetailScale // Use physical constraint instead of interpolation
  };

  // Absolute minimums are now effectively disabled as we use ResolutionBlocker
  // to prevent usage on screens that are too small.
  // We keep non-zero values just to prevent math errors.
  const ABSOLUTE_MINIMUMS = {
    DETAIL_VISIBLE: 0.001,
    HIGH_DETAIL: 0.002,
    GRID_DENSITY: 0.003,
    RULER_DETAIL: 0.004
  };

  // Use the HIGHER of percentage-based or absolute minimum
  const thresholds = {
    DETAIL_VISIBLE: Math.max(percentageBased.DETAIL_VISIBLE, ABSOLUTE_MINIMUMS.DETAIL_VISIBLE),
    HIGH_DETAIL: Math.max(percentageBased.HIGH_DETAIL, ABSOLUTE_MINIMUMS.HIGH_DETAIL),
    GRID_DENSITY: Math.max(percentageBased.GRID_DENSITY, ABSOLUTE_MINIMUMS.GRID_DENSITY),
    RULER_DETAIL: Math.max(percentageBased.RULER_DETAIL, ABSOLUTE_MINIMUMS.RULER_DETAIL)
  };

  return thresholds;
}

// Legacy export for backward compatibility (will be replaced by dynamic thresholds)
// These are now just fallback values
export const ZOOM_THRESHOLDS = {
  DETAIL_VISIBLE: 0.8,
  HIGH_DETAIL: 1.2,
  GRID_DENSITY: 1.5,
  RULER_DETAIL: 1.8
};

export const ZOOM_LEVELS = {
  OVERVIEW: { min: 0.01, max: ZOOM_THRESHOLDS.DETAIL_VISIBLE, name: 'Overview' },
  DETAIL: { min: ZOOM_THRESHOLDS.DETAIL_VISIBLE, max: 5, name: 'Detail' }
};

export class ZoomLevelManager {
  constructor(onLevelChange) {
    this.currentLevel = 'OVERVIEW';
    this.currentScale = 1;
    this.onLevelChange = onLevelChange;
    // Dynamic thresholds will be set via setThresholds()
    this.thresholds = ZOOM_THRESHOLDS; // Fallback to static initially
  }

  /**
   * Update the dynamic thresholds based on current zoom bounds
   * Should be called whenever zoom bounds change (layout recalc, resize, etc.)
   */
  setThresholds(minScale, maxScale, layoutPixelsPerYear = null) {
    this.thresholds = calculateThresholds(minScale, maxScale, layoutPixelsPerYear);
  }

  updateScale(scale) {
    this.currentScale = scale;
    const newLevel = this.determineLevel(scale);

    if (newLevel !== this.currentLevel) {
      this.currentLevel = newLevel;
      this.onLevelChange(newLevel, scale);
    }
  }

  determineLevel(scale) {
    if (scale < this.thresholds.DETAIL_VISIBLE) {
      return 'OVERVIEW';
    }
    return 'DETAIL';
  }

  shouldShowDetail() {
    return this.currentLevel === 'DETAIL';
  }

  /**
   * Get current threshold values
   * Useful for rendering functions that need to check thresholds
   */
  getThresholds() {
    return this.thresholds;
  }
}
