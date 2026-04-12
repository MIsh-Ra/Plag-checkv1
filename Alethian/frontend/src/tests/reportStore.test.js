import { describe, it, expect } from 'vitest';
import { useReportStore } from '../stores/reportStore';

describe('reportStore', () => {
    it('sets selected match', () => {
        const { setSelectedMatch } = useReportStore.getState();
        setSelectedMatch('match-123');
        expect(useReportStore.getState().selectedMatchId).toBe('match-123');
    });

    it('toggles filter type', () => {
        const { toggleFilterType } = useReportStore.getState();
        // web starts as true
        expect(useReportStore.getState().filterTypes.web).toBe(true);
        toggleFilterType('web');
        expect(useReportStore.getState().filterTypes.web).toBe(false);
        toggleFilterType('web');
        expect(useReportStore.getState().filterTypes.web).toBe(true);
    });
});
