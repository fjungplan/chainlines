import * as d3 from 'd3';

export class JerseyRenderer {
  /**
   * Create a gradient definition for a specific era (scaled to 100% of the era's container)
   */
  static createEraGradient(svg, era, idPrefix) {
    const sponsors = era.sponsors || [];
    if (sponsors.length === 0) return null;

    const gradientId = `${idPrefix}-gradient`;

    // Check if gradient already exists
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs');
    if (!defs.select(`#${gradientId}`).empty()) return gradientId;

    const gradient = defs.append('linearGradient')
      .attr('id', gradientId)
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');

    let cumulativePercent = 0;

    // Normalize prominence to ensure we fill 100% of the bar
    // (If user data doesn't sum to 100, we scale it)
    const totalProminence = sponsors.reduce((sum, s) => sum + (parseFloat(s.prominence) || 0), 0) || 100;

    // DEBUG: Log gradient generation to debug generic patterns
    if (Math.random() < 0.05) { // Sample logs to avoid spamming
      console.log(`[JerseyRenderer] Gradient ${gradientId} - Total: ${totalProminence}`, sponsors);
    }

    sponsors.forEach((sponsor) => {
      const prominence = parseFloat(sponsor.prominence) || 0;
      const percent = (prominence / totalProminence) * 100;

      const startPercent = cumulativePercent;
      const endPercent = cumulativePercent + percent;

      gradient.append('stop')
        .attr('offset', `${startPercent}%`)
        .attr('stop-color', sponsor.color);
      gradient.append('stop')
        .attr('offset', `${endPercent}%`)
        .attr('stop-color', sponsor.color);

      cumulativePercent = endPercent;
    });

    // Fill remaining space if any (floating point errors)
    if (cumulativePercent < 100) {
      const lastSponsor = sponsors[sponsors.length - 1];
      gradient.append('stop')
        .attr('offset', `${cumulativePercent}%`)
        .attr('stop-color', lastSponsor.color);
      gradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', lastSponsor.color);
    }

    return gradientId;
  }

  static createGradientDefinition(svg, node) {
    // DEPRECATED: Used for whole-node gradients
    const gradientId = `gradient-${node.id}`;
    const latestEra = node.eras[node.eras.length - 1];
    return this.createEraGradient(svg, latestEra, gradientId);
  }

  static renderNode(nodeGroup, node, svg) {
    const gradientId = this.createGradientDefinition(svg, node);
    const rect = nodeGroup.append('rect')
      .attr('width', node.width)
      .attr('height', node.height)
      .attr('rx', 0.5)
      .attr('ry', 0.5)
      .attr('shape-rendering', 'crispEdges');
    if (gradientId) {
      rect.attr('fill', `url(#${gradientId})`);
    } else {
      rect.attr('fill', '#5a5a5a');
    }
    return rect;
  }

  static createShadowFilter(svg) {
    const defs = svg.select('defs').empty() ? svg.append('defs') : svg.select('defs');
    defs.select('#drop-shadow').remove();
    defs.select('#underglow').remove();

    const filter = defs.append('filter')
      .attr('id', 'drop-shadow')
      .attr('height', '200%')
      .attr('width', '200%')
      .attr('x', '-50%')
      .attr('y', '-50%');
    filter.append('feGaussianBlur')
      .attr('in', 'SourceAlpha')
      .attr('stdDeviation', 2)
      .attr('result', 'blur');
    filter.append('feOffset')
      .attr('dx', 2)
      .attr('dy', 2)
      .attr('in', 'blur')
      .attr('result', 'offsetblur');
    filter.append('feFlood')
      .attr('flood-color', '#000')
      .attr('flood-opacity', 0.35)
      .attr('result', 'shadowColor');
    filter.append('feComposite')
      .attr('in', 'shadowColor')
      .attr('in2', 'offsetblur')
      .attr('operator', 'in')
      .attr('result', 'shadow');
    const feMerge = filter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'shadow');

    // Underglow filter for hover effect - tight glow hugging the shape
    const glowFilter = defs.append('filter')
      .attr('id', 'underglow')
      .attr('height', '200%')
      .attr('width', '200%')
      .attr('x', '-50%')
      .attr('y', '-50%');
    // Dilate very slightly to create tight glow base
    glowFilter.append('feMorphology')
      .attr('in', 'SourceGraphic')
      .attr('operator', 'dilate')
      .attr('radius', '0.5')
      .attr('result', 'expanded');
    glowFilter.append('feGaussianBlur')
      .attr('in', 'expanded')
      .attr('stdDeviation', 3)
      .attr('result', 'blur');
    glowFilter.append('feFlood')
      .attr('flood-color', '#FFD700')
      .attr('flood-opacity', 0.9)
      .attr('result', 'color');
    glowFilter.append('feComposite')
      .attr('in', 'color')
      .attr('in2', 'blur')
      .attr('operator', 'in')
      .attr('result', 'glow');
    const glowMerge = glowFilter.append('feMerge');
    glowMerge.append('feMergeNode').attr('in', 'glow');
    glowMerge.append('feMergeNode').attr('in', 'SourceGraphic');
  }

  static addNodeLabel(nodeGroup, node) {
    const latestEra = node.eras[node.eras.length - 1];
    const name = latestEra.name || 'Unknown Team';
    const displayName = name.length > 25 ? name.substring(0, 22) + '...' : name;
    const teamNameText = nodeGroup.append('text')
      .attr('x', node.width / 2)
      .attr('y', node.height / 2)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-family', 'Montserrat, sans-serif')
      .attr('font-size', '11px')
      .attr('font-weight', '700')
      .text(displayName);
    // Font: Montserrat bold (weight 700), size 11px
    const yearRange = node.dissolution_year
      ? `${node.founding_year}-${node.dissolution_year}`
      : `${node.founding_year}-`;
    nodeGroup.append('text')
      .attr('x', node.width / 2)
      .attr('y', node.height / 2 + 14)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('fill', 'white')
      .attr('font-family', 'Montserrat, sans-serif')
      .attr('font-size', '9px')
      .attr('font-weight', '400')
      .text(yearRange);
    // Font: Montserrat regular (weight 400), size 9px
  }
}
