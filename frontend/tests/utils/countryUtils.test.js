
import { describe, it, expect } from 'vitest';
import { getCountryCode } from '../../src/utils/countryUtils';

describe('countryUtils', () => {
    describe('getCountryCode', () => {
        it('returns lowercase alpha-2 code for valid uppercase alpha-3', () => {
            expect(getCountryCode('FRA')).toBe('fr');
            expect(getCountryCode('USA')).toBe('us');
            expect(getCountryCode('BEL')).toBe('be');
        });

        it('returns lowercase alpha-2 code for valid lowercase alpha-3', () => {
            expect(getCountryCode('fra')).toBe('fr');
            expect(getCountryCode('ita')).toBe('it');
        });

        it('returns null for unknown codes', () => {
            expect(getCountryCode('XYZ')).toBe(null);
            expect(getCountryCode('XXX')).toBe(null);
        });

        it('returns null for null or empty input', () => {
            expect(getCountryCode(null)).toBe(null);
            expect(getCountryCode('')).toBe(null);
            expect(getCountryCode(undefined)).toBe(null);
        });
    });
});
