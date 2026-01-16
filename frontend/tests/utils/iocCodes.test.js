import { describe, it, expect } from 'vitest';
import { getCountryFlag } from '../../src/utils/iocCodes';

describe('getCountryFlag', () => {
    it('returns ISO2 code for standard IOC codes', () => {
        expect(getCountryFlag('FRA')).toBe('fr');
        expect(getCountryFlag('USA')).toBe('us');
    });

    it('returns correct mappings for irregular codes', () => {
        expect(getCountryFlag('GER')).toBe('de'); // IOC: GER -> ISO: DE
        expect(getCountryFlag('NED')).toBe('nl'); // IOC: NED -> ISO: NL
        expect(getCountryFlag('SUI')).toBe('ch'); // IOC: SUI -> ISO: CH
        expect(getCountryFlag('DEN')).toBe('dk'); // IOC: DEN -> ISO: DK
        expect(getCountryFlag('RSA')).toBe('za'); // IOC: RSA -> ISO: ZA
    });

    it('is case insensitive', () => {
        expect(getCountryFlag('fra')).toBe('fr');
        expect(getCountryFlag('GeR')).toBe('de');
    });

    it('returns null for unknown codes', () => {
        expect(getCountryFlag('XXX')).toBeNull();
        expect(getCountryFlag('')).toBeNull();
        expect(getCountryFlag(null)).toBeNull();
    });
});
