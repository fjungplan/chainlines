import * as d3 from 'd3';
import { ZOOM_THRESHOLDS } from './zoomLevelManager';
import { JerseyRenderer } from './jerseyRenderer';

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

  static renderEraTimeline(nodeGroup, node, scale, svg, onEraHover, onEraHoverEnd) {
    const eras = node.eras;
    if (!eras || eras.length === 0) {
      nodeGroup.selectAll('.era-segment').remove();
      return;
    }

    if (scale < ZOOM_THRESHOLDS.DETAIL_VISIBLE) {
      nodeGroup.selectAll('.era-segment').remove();
      return;
    }

    // Use full height for eras
    const timelineHeight = node.height;
    const y = 0;
    const startYear = eras[0].year;

    // Calculate effective end year
    const currentYear = new Date().getFullYear();
    const effectiveEndYear = node.dissolution_year
      ? node.dissolution_year + 1
      : currentYear + 1;
    const totalYears = effectiveEndYear - startYear;

    if (totalYears <= 0) return;

    // Prepare data with pre-calculated positions to keep join clean
    const eraData = eras.map((era, index) => {
      const nextEra = eras[index + 1];
      const eraEndYear = nextEra ? nextEra.year : effectiveEndYear;
      const eraDuration = eraEndYear - era.year;

      if (eraDuration <= 0) return null;

      const width = (eraDuration / totalYears) * node.width;
      const x = ((era.year - startYear) / totalYears) * node.width;

      // Determine fill style based on zoom level
      let fillStyle = '#ccc';
      if (scale >= ZOOM_THRESHOLDS.HIGH_DETAIL && svg) {
        // High zoom: Use jersey gradient
        // Ensure ID is safe for CSS selectors (cannot start with number)
        const uniqueId = `nid-${era.id || node.id}-${index}`;
        const gradientId = JerseyRenderer.createEraGradient(svg, era, uniqueId);
        if (gradientId) {
          fillStyle = `url(#${gradientId})`;
        } else {
          fillStyle = era.sponsors?.[0]?.color || '#ccc';
        }
      } else {
        // Medium zoom (0.8 - 1.2): Use solid color
        fillStyle = era.sponsors?.[0]?.color || '#ccc';
      }

      return {
        id: era.id || `${node.id}-era-${index}`, // Ensure unique key if possible
        x,
        y: 0, // Top of node
        width: Math.max(0, width),
        height: timelineHeight,
        fill: fillStyle,
        originalEra: era // Pass original era object for tooltip
      };
    }).filter(d => d !== null);

    nodeGroup.selectAll('.era-segment')
      .data(eraData, d => d.id)
      .join(
        enter => enter.insert('rect', 'text') // Insert before text labels
          .attr('class', 'era-segment')
          .attr('rx', 0.5) // Optional: match node border radius if wanted
          .attr('ry', 0.5)
          .attr('shape-rendering', 'crispEdges')
          .attr('opacity', 1)
          .attr('x', d => d.x)
          .attr('y', d => d.y)
          .attr('width', d => d.width)
          .attr('height', d => d.height)
          .attr('fill', d => d.fill)
          .style('cursor', 'pointer') // Indicate interactability
          .on('mouseenter', (event, d) => {
            if (onEraHover) onEraHover(event, d.originalEra, node);
          })
          .on('mousemove', (event, d) => {
            // Ensure tooltip follows mouse if handled by parent state
            if (onEraHover) onEraHover(event, d.originalEra, node);
            // Note: optimization - parent usually tracks movement via separate handler or this one just updates position?
            // TimelineGraph uses single Tooltip state. If we call onEraHover again it updates position.
            // Actually TimelineGraph `handleEraHover` sets state. Calling it on mousemove updates position.
          })
          .on('mouseleave', (event) => {
            if (onEraHoverEnd) onEraHoverEnd(event);
          }),
        update => update
          .attr('x', d => d.x)
          .attr('y', d => d.y)
          .attr('width', d => d.width)
          .attr('height', d => d.height)
          .attr('fill', d => d.fill),
        exit => exit.remove()
      );
  }
}
