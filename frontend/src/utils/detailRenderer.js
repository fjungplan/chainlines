import * as d3 from 'd3';
import { ZOOM_LEVELS } from './zoomLevelManager';

export class DetailRenderer {
  /**
   * Render detailed link types when zoomed in
   */
  static renderDetailedLinks(g, links, scale) {
    // IMPORTANT: Viscous connectors have filled blobs + dotted outline paths.
    // Keep fills fully opaque and avoid changing overall opacity here.
    g.selectAll('.links path.link-outline-top, .links path.link-outline-bottom')
      .attr('stroke-width', d => {
        const baseWidth = 2;
        // Thicker lines for merges/splits
        const multiplier = (d.type === 'MERGE' || d.type === 'SPLIT') ? 1.5 : 1;
        return baseWidth * multiplier;
      });

    g.selectAll('.links path.link-fill')
      .attr('opacity', 1);

    // Arrowheads removed for Viscous Connectors
    // this.addArrowheads(g, links);
  }

  static addArrowheads(g, links) {
    // Deprecated for Viscous Connectors
  }

  /**
   * Add era timeline within node at detail level
   */
  static renderEraTimeline(nodeGroup, node, scale) {
    if (scale < ZOOM_LEVELS.DETAIL.min) return;

    const eras = node.eras;
    if (!eras || eras.length <= 1) return;

    const timelineHeight = 4;
    const y = node.height - timelineHeight - 5;

    // Calculate era widths
    // Calculate end year for the timeline (start of next year if dissolved, or next year if active)
    const currentYear = new Date().getFullYear();
    const effectiveEndYear = node.dissolution_year
      ? node.dissolution_year + 1
      : currentYear + 1;

    // Calculate total duration based on node start/end, which matches how width is calculated
    const startYear = eras[0].year;
    const totalYears = effectiveEndYear - startYear;

    if (totalYears <= 0) return;

    eras.forEach((era, index) => {
      const nextEra = eras[index + 1];

      // Determine end of this era segment
      // If there is a next era, this one ends when the next one starts
      // If this is the last era, it ends at the node's end year
      const eraEndYear = nextEra ? nextEra.year : effectiveEndYear;

      const eraDuration = eraEndYear - era.year;

      // Sanity check for negative duration (shouldn't happen with sorted eras)
      if (eraDuration <= 0) return;

      const width = (eraDuration / totalYears) * node.width;
      const x = ((era.year - startYear) / totalYears) * node.width;

      nodeGroup.append('rect')
        .attr('class', 'era-segment')
        .attr('x', x)
        .attr('y', y)
        .attr('width', Math.max(0, width - 1)) // -1 for small gap between segments
        .attr('height', timelineHeight)
        .attr('fill', era.sponsors?.[0]?.color || '#ccc')
        .attr('opacity', 0.8)
        .attr('rx', 1)
        .attr('ry', 1);
    });
  }
}
