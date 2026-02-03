import React from 'react';

export class TooltipBuilder {
  static buildNodeTooltip(node) {
    const latestEra = node.eras?.[node.eras.length - 1] || {};
    const sponsors = latestEra.sponsors || [];

    return (
      <div className="timeline-tooltip-metadata node-summary">
        <h4>{latestEra.name || 'Unknown Team'}</h4>
        <div className="timeline-tooltip-row">
          <span className="label">Timeline:</span>
          <span className="value">{node.founding_year} – {node.dissolution_year || 'Present'}</span>
        </div>

        {sponsors.length > 0 && (
          <div className="timeline-tooltip-section">
            <div className="label">Current/Latest Sponsors:</div>
            <ul className="timeline-tooltip-sponsor-list">
              {sponsors.map((s, i) => (
                <li key={i}>
                  <span
                    className="timeline-tooltip-sponsor-dot"
                    style={{ backgroundColor: s.color || s.hex_color || '#888' }}
                  />
                  {s.brand || s.name} ({s.prominence}%)
                </li>
              ))}
            </ul>
          </div>
        )}
        <div className="timeline-tooltip-hint">Click for full history • Zoom in for details</div>
      </div>
    );
  }

  static buildEraTooltip(era, node) {
    const sponsors = era.sponsors || [];
    return (
      <div className="timeline-tooltip-metadata era-detail">
        <h4>{era.name || era.registered_name || 'Unknown Team'}</h4>
        <div className="timeline-tooltip-row">
          <span className="label">Year:</span>
          <span className="value">{era.year || era.season_year}</span>
          {/* If we knew end year here easily without looking at next era... 
               The DetailRenderer calculates it. We might just show start year or if passed in context.
               For now, showing Start Year is safe. 
               The requirement said "show one additional detail: the current year".
           */}
        </div>
        {sponsors.length > 0 && (
          <div className="timeline-tooltip-section">
            <div className="label">Sponsors:</div>
            <ul className="timeline-tooltip-sponsor-list">
              {sponsors.map((s, i) => (
                <li key={i}>
                  <span
                    className="timeline-tooltip-sponsor-dot"
                    style={{ backgroundColor: s.color || s.hex_color || '#888' }}
                  />
                  {s.brand || s.name} ({s.prominence}%)
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  }

  static buildLinkTooltip(link, nodes) {
    const sourceNode = nodes?.find(n => n.id === link.source);
    const targetNode = nodes?.find(n => n.id === link.target);

    if (!sourceNode || !targetNode) return null;

    // Helper to get Team Name (Display > Legal > Fallback)
    const getTeamName = (node) => node.display_name || node.legal_name || node.eras?.[0]?.name || 'Unknown Team';

    // Helper to get Era Name with fallback
    const getRelevantEraName = (node, targetYear, isPredecessor) => {
      if (!node?.eras || node.eras.length === 0) return 'Unknown Era';

      const year = parseInt(targetYear, 10);

      // 1. Try exact match
      const exact = node.eras.find(e => e.year === year);
      if (exact) return exact.name;

      // 2. Fallback: Find closest logic
      // For Predecessor: The latest era (assume it led to this event)
      // For Successor: The earliest era (start of new lineage)
      if (isPredecessor) {
        // Find max year
        return node.eras.reduce((prev, current) => (prev.year > current.year) ? prev : current).name;
      } else {
        // Find min year
        return node.eras.reduce((prev, current) => (prev.year < current.year) ? prev : current).name;
      }
    };

    const sourceTeamName = getTeamName(sourceNode);
    const targetTeamName = getTeamName(targetNode);

    // Predecessor: Era from year BEFORE the event (or last available)
    const sourceEraName = link.year ? getRelevantEraName(sourceNode, parseInt(link.year) - 1, true) : 'Unknown Era';

    // Successor: Era from year OF the event (or first available)
    const targetEraName = link.year ? getRelevantEraName(targetNode, parseInt(link.year), false) : 'Unknown Era';

    return (
      <div className="timeline-tooltip-metadata">
        <h4>{this.getEventTypeName(link.type)}</h4>
        <div className="timeline-tooltip-row">
          <span className="label">From:</span>
          <span className="value">{sourceTeamName} <span className="timeline-tooltip-era-hint">({sourceEraName})</span></span>
        </div>
        <div className="timeline-tooltip-row">
          <span className="label">To:</span>
          <span className="value">{targetTeamName} <span className="timeline-tooltip-era-hint">({targetEraName})</span></span>
        </div>
        <div className="timeline-tooltip-row">
          <span className="label">Year:</span>
          <span className="value">{link.year}</span>
        </div>
        {link.notes && (
          <div className="timeline-tooltip-section">
            <div className="label">Notes:</div>
            <p className="timeline-tooltip-notes">{link.notes}</p>
          </div>
        )}
      </div>
    );
  }

  static getTierName(tier) {
    const names = {
      1: 'UCI WorldTour',
      2: 'UCI ProTeam',
      3: 'UCI Continental'
    };
    return names[tier] || 'Unknown';
  }

  static getEventTypeName(type) {
    const names = {
      'LEGAL_TRANSFER': 'Legal Transfer',
      'SPIRITUAL_SUCCESSION': 'Spiritual Succession',
      'MERGE': 'Team Merger',
      'SPLIT': 'Team Split'
    };
    return names[type] || type;
  }
}
