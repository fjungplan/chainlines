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
    const cleanName = name.length > 30 ? name.substring(0, 27) + '...' : name; // Hard clip safety

    // 1. Calculate available dimensions
    const w = node.width; // Virtual coordinates
    const h = node.height;

    // 2. Define sizing constants relative to node height
    // Standard ratio: Text takes up ~35% of height
    const baseFontSize = Math.max(h * 0.35, 1);
    const minFontSize = baseFontSize * 0.6; // Allow shrinking to 60% of base

    const yearFontSize = baseFontSize * 0.7;
    const lineHeight = 1.1; // em

    // 3. Helper to measure text width (approximate heuristic for standard fonts)
    // Avg char width is roughly 0.6em for mixed case
    const measureText = (text, size) => text.length * (size * 0.6);

    // 4. Fitting strategy
    // Strategy A: Single Line
    // Strategy B: Wrapped (2 lines)
    // Strategy C: Shrink Single Line
    // Strategy D: Shrink Wrapped

    let lines = [cleanName];
    let finalFontSize = baseFontSize;
    let isWrapped = false;

    const singleLineWidth = measureText(cleanName, baseFontSize);
    const availableWidth = w * 0.9; // 10% padding

    if (singleLineWidth > availableWidth) {
      // Try Wrapping
      const words = cleanName.split(/\s+/);
      if (words.length > 1) {
        const mid = Math.ceil(words.length / 2);
        const line1 = words.slice(0, mid).join(' ');
        const line2 = words.slice(mid).join(' ');

        // Check if wrapped fits at base size
        const w1 = measureText(line1, baseFontSize);
        const w2 = measureText(line2, baseFontSize);

        if (Math.max(w1, w2) <= availableWidth) {
          lines = [line1, line2];
          isWrapped = true;
        } else {
          // Wrapped still too big? Try shrinking wrapped
          // Calculate scale factor needed
          const maxLineW = Math.max(w1, w2);
          const scale = availableWidth / maxLineW;
          if (baseFontSize * scale >= minFontSize) {
            finalFontSize = baseFontSize * scale;
            lines = [line1, line2];
            isWrapped = true;
          } else {
            // Too small even wrapped? Fallback to single line shrunk (or truncated eventually)
            const scaleSingle = availableWidth / singleLineWidth;
            finalFontSize = Math.max(baseFontSize * scaleSingle, minFontSize);
            lines = [cleanName]; // Revert to single line
          }
        }
      } else {
        // Single word, just shrink
        const scale = availableWidth / singleLineWidth;
        finalFontSize = Math.max(baseFontSize * scale, minFontSize);
      }
    }

    // 5. Render Team Name
    const textGroup = nodeGroup.append('text')
      .attr('x', w / 2)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-family', 'Montserrat, sans-serif')
      .attr('font-weight', '700')
      .attr('font-size', `${finalFontSize}px`)
      .style('text-shadow', '0 2px 4px rgba(0,0,0,0.9)'); // Shadow for contrast

    if (isWrapped) {
      // Center vertical: -0.5 line height lift
      textGroup.append('tspan')
        .attr('x', w / 2)
        .attr('dy', `-${(finalFontSize * lineHeight) * 0.55}`) // Slightly higher lift
        .text(lines[0]);

      textGroup.append('tspan')
        .attr('x', w / 2)
        .attr('dy', `${finalFontSize * lineHeight}`)
        .text(lines[1]);

      // Center the whole group vertically
      textGroup.attr('y', h / 2);
    } else {
      textGroup.attr('y', h / 2)
        .attr('dominant-baseline', 'middle')
        .text(lines[0]);
    }

    // 6. Render Year Range (Only if there's space)
    // If we wrapped, we used more vertical space.
    // If node is very short, skip year range.

    // Height Check:
    // Wrapped takes: 2 lines * 1.1 = 2.2em
    // Year range needs: 1 line ~ 1em
    // Total needed: ~3.5em (with gap)

    // Available height is h.
    // finalFontSize is our 'em'.
    // If h < 3.5 * finalFontSize, hide years?

    const requiredHeightForYears = isWrapped
      ? (finalFontSize * 3.5)
      : (finalFontSize * 2.5);

    if (h > requiredHeightForYears) {
      const yearRange = node.dissolution_year
        ? `${node.founding_year}-${node.dissolution_year}`
        : `${node.founding_year}-`;

      const yearY = isWrapped
        ? (h / 2) + (finalFontSize * lineHeight * 1.2) // Tighter gap (was 1.5)
        : (h / 2) + (finalFontSize * 1.0);             // Tighter gap (was 1.2)

      nodeGroup.append('text')
        .attr('x', w / 2)
        .attr('y', yearY)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', 'rgba(255,255,255,0.9)') // Brighter for better contrast
        .attr('font-family', 'Montserrat, sans-serif')
        .attr('font-size', `${yearFontSize}px`)
        .attr('font-weight', '400')
        .style('text-shadow', '0 2px 4px rgba(0,0,0,0.9)') // Shadow for contrast
        .text(yearRange);
    }
  }
}
