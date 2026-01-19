import { describe, it, expect, beforeEach, vi } from 'vitest';
import { calculateYearRange, createXScale } from '../../../src/utils/layout/utils/scales';

describe('scales', () => {
    describe('calculateYearRange', () => {
        it('should calculate range from node eras', () => {
            const nodes = [
                {
                    founding_year: 2000,
                    dissolution_year: 2010,
                    eras: [
                        { year: 2000 },
                        { year: 2005 },
                        { year: 2010 }
                    ]
                },
                {
                    founding_year: 1995,
                    dissolution_year: 2005,
                    eras: [
                        { year: 1995 },
                        { year: 2000 }
                    ]
                }
            ];

            const result = calculateYearRange(nodes);

            expect(result).toHaveProperty('min');
            expect(result).toHaveProperty('max');
            expect(result.min).toBeLessThanOrEqual(1995);
            expect(result.max).toBeGreaterThanOrEqual(2010);
        });

        it('should handle nodes without dissolution years', () => {
            const currentYear = new Date().getFullYear();
            const nodes = [
                {
                    founding_year: 2020,
                    dissolution_year: null,
                    eras: [
                        { year: 2020 },
                        { year: 2023 }
                    ]
                }
            ];

            const result = calculateYearRange(nodes);

            expect(result.min).toBeLessThanOrEqual(2020);
            // Should extend to current year + 1
            expect(result.max).toBeGreaterThanOrEqual(currentYear);
        });

        it('should use current year as max when appropriate', () => {
            const currentYear = new Date().getFullYear();
            const nodes = [
                {
                    founding_year: 1900,
                    dissolution_year: 1950,
                    eras: [{ year: 1900 }]
                }
            ];

            const result = calculateYearRange(nodes);

            // Should include current year for active teams
            expect(result.max).toBeGreaterThanOrEqual(currentYear);
        });

        it('should handle empty node arrays', () => {
            const nodes = [];
            const currentYear = new Date().getFullYear();

            const result = calculateYearRange(nodes);

            // Should have fallback values
            expect(result.min).toBe(1900);
            expect(result.max).toBe(currentYear + 1);
        });

        it('should add +1 to max year for full span', () => {
            const nodes = [
                {
                    founding_year: 2000,
                    dissolution_year: 2010,
                    eras: [{ year: 2000 }]
                }
            ];

            const result = calculateYearRange(nodes);

            // Max should be dissolution year + 1
            expect(result.max).toBeGreaterThan(2010);
        });
    });

    describe('createXScale', () => {
        it('should create correct scale with padding', () => {
            const width = 1000;
            const yearRange = { min: 2000, max: 2010 };
            const stretchFactor = 1;

            const xScale = createXScale(width, yearRange, stretchFactor);

            // Test that it's a function
            expect(typeof xScale).toBe('function');

            // Test boundary values
            const minX = xScale(yearRange.min);
            const maxX = xScale(yearRange.max);

            // Should have padding (50px default)
            expect(minX).toBeGreaterThan(0);
            expect(maxX).toBeLessThan(width);

            // Should be monotonically increasing
            expect(xScale(2005)).toBeGreaterThan(minX);
            expect(xScale(2005)).toBeLessThan(maxX);
        });

        it('should apply stretch factor correctly', () => {
            const width = 1000;
            const yearRange = { min: 2000, max: 2010 };

            const xScale1 = createXScale(width, yearRange, 1);
            const xScale2 = createXScale(width, yearRange, 2);

            // With stretch factor 2, the span should be wider
            const span1 = xScale1(2010) - xScale1(2000);
            const span2 = xScale2(2010) - xScale2(2000);

            expect(span2).toBeGreaterThan(span1);
            expect(span2).toBeCloseTo(span1 * 2, 0);
        });

        it('should handle single year range', () => {
            const width = 1000;
            const yearRange = { min: 2000, max: 2001 };
            const stretchFactor = 1;

            const xScale = createXScale(width, yearRange, stretchFactor);

            // Should not throw
            expect(() => xScale(2000)).not.toThrow();
            expect(() => xScale(2001)).not.toThrow();
        });

        it('should return consistent values for same input', () => {
            const width = 1000;
            const yearRange = { min: 2000, max: 2010 };
            const stretchFactor = 1;

            const xScale = createXScale(width, yearRange, stretchFactor);

            const x1 = xScale(2005);
            const x2 = xScale(2005);

            expect(x1).toBe(x2);
        });
    });
});
