export const ZOOM_THRESHOLDS = {
  DETAIL_VISIBLE: 0.8,   // Reveal text/eras
  HIGH_DETAIL: 1.2,      // Gradient eras, 1yr grid
  GRID_DENSITY: 1.5,     // Dotted vs dashed grid
  RULER_DETAIL: 1.8      // Annual ruler labels
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
    if (scale < ZOOM_THRESHOLDS.DETAIL_VISIBLE) {
      return 'OVERVIEW';
    }
    return 'DETAIL';
  }

  shouldShowDetail() {
    return this.currentLevel === 'DETAIL';
  }
}
