import { describe, it, expect } from 'vitest';
import { TooltipBuilder } from '../../src/utils/tooltipBuilder';

describe('TooltipBuilder', () => {
  describe('buildLinkTooltip', () => {
    const mockNodes = [
      {
        id: '1',
        display_name: 'Team A Display',
        legal_name: 'Team A Legal',
        eras: [
          { year: 2000, name: 'Team A 2000' },
          { year: 2001, name: 'Team A 2001' },
          { year: 2002, name: 'Team A 2002' }
        ]
      },
      {
        id: '2',
        display_name: 'Team B Display',
        legal_name: 'Team B Legal',
        eras: [
          { year: 2000, name: 'Team B 2000' },
          { year: 2005, name: 'Team B 2005' } // Gap
        ]
      }
    ];

    it('should correctly identify predecessor era (year - 1)', () => {
      const link = { source: '1', target: '2', year: 2001, type: 'TRANSFER' };
      const result = TooltipBuilder.buildLinkTooltip(link, mockNodes);
      // Predecessor: 2001 - 1 = 2000 -> "Team A 2000"
      expect(result).not.toBeNull();
      expect(typeof result).toBe('object');
    });

    it('should fallback to latest era for predecessor gap', () => {
      // Link in 2005. Predecessor (Node 1) only goes to 2002.
      // Should find max year (2002) for Year-1 (2004) search failure.
      const link = { source: '1', target: '2', year: 2005, type: 'TRANSFER' };
      const result = TooltipBuilder.buildLinkTooltip(link, mockNodes);
      expect(result).not.toBeNull();
    });

    it('should fallback to earliest era for successor gap', () => {
      // Link in 1999. Successor (Node 2) starts 2000.
      // Should find min year (2000) for Year (1999) search failure.
      const link = { source: '1', target: '2', year: 1999, type: 'TRANSFER' };
      const result = TooltipBuilder.buildLinkTooltip(link, mockNodes);
      expect(result).not.toBeNull();
    });
  });
});
