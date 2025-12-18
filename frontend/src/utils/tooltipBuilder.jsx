import React from 'react';

export class TooltipBuilder {
  static buildNodeTooltip(node) {
    const latestEra = node.eras?.[node.eras.length - 1] || {};
    const sponsors = latestEra.sponsors || [];

    return (
      <div className="tooltip-content node-summary">
        <h4>{latestEra.name || 'Unknown Team'}</h4>
        <div className="tooltip-row">
          <span className="label">Founded:</span>
          <span className="value">{node.founding_year}</span>
        </div>
        {node.dissolution_year && (
          <div className="tooltip-row">
            <span className="label">Dissolved:</span>
            <span className="value">{node.dissolution_year}</span>
          </div>
        )}
        <div className="tooltip-hint">Click for full history • Zoom in for details</div>
      </div>
    );
  }

  static buildEraTooltip(era, node) {
    const sponsors = era.sponsors || [];
    return (
      <div className="tooltip-content era-detail">
        <h4>{era.name || 'Unknown Intent'}</h4>
        <div className="tooltip-row">
          <span className="label">Year:</span>
          <span className="value">{era.year}</span>
          {/* If we knew end year here easily without looking at next era... 
               The DetailRenderer calculates it. We might just show start year or if passed in context.
               For now, showing Start Year is safe. 
               The requirement said "show one additional detail: the current year".
           */}
        </div>
        {sponsors.length > 0 && (
          <div className="tooltip-section">
            <div className="label">Sponsors:</div>
            <ul className="sponsor-list">
              {sponsors.map((s, i) => (
                <li key={i}>
                  <span
                    className="sponsor-dot"
                    style={{ backgroundColor: s.color }}
                  />
                  {s.brand} ({s.prominence}%)
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

    const sourceName = sourceNode.eras?.[sourceNode.eras.length - 1]?.name;
    const targetName = targetNode.eras?.[0]?.name;

    return (
      <div className="tooltip-content">
        <h4>{this.getEventTypeName(link.type)}</h4>
        <div className="tooltip-row">
          <span className="label">From:</span>
          <span className="value">{sourceName}</span>
        </div>
        <div className="tooltip-row">
          <span className="label">To:</span>
          <span className="value">{targetName}</span>
        </div>
        <div className="tooltip-row">
          <span className="label">Year:</span>
          <span className="value">{link.year}</span>
        </div>
        {link.notes && (
          <div className="tooltip-section">
            <div className="label">Notes:</div>
            <p className="notes">{link.notes}</p>
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
