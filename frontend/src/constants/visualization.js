export const VISUALIZATION = {
  // Dimensions
  MIN_NODE_WIDTH: 100,
  NODE_HEIGHT: 40, // Base/Default height - overridden by dynamic calc
  HEIGHT_FACTOR: 1, // Node height = pixelsPerYear * HEIGHT_FACTOR
  LINK_STROKE_WIDTH: 2,

  // Colors
  LINK_COLOR_LEGAL: '#333',
  LINK_COLOR_SPIRITUAL: '#999',

  // Zoom - Dynamic bounds
  ZOOM_MIN_FALLBACK: 0.5,  // Absolute floor if calculation fails
  ZOOM_MAX_FALLBACK: 5,    // Absolute ceiling if calculation fails

  // Max zoom constraints (whichever is more restrictive)
  MAX_ZOOM_YEAR_SPAN: 10,      // Show at least this many years width
  MAX_ZOOM_SWIMLANES: 2,       // Show at least this many swimlanes height

  // Spacing
  YEAR_WIDTH: 120,  // Horizontal spacing per year
  TIER_SPACING: 100, // Vertical spacing between tiers

  // Animation
  TRANSITION_DURATION: 300,
};
