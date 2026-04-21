import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import FilterBar from '../components/report/FilterBar';
import { useReportStore } from '../stores/reportStore';

describe('FilterBar Component', () => {
    beforeEach(() => {
        // Reset store state before each test
        useReportStore.setState({
            filterTypes: {
                internal_exact: true,
                internal_paraphrase: true,
                web: true,
                excluded: false
            }
        });
    });

    it('toggles Zustand store filter values', () => {
        render(<FilterBar />);

        // Find and click one of the real checkbox labels
        const webCheckbox = screen.getByLabelText(/Web Dragnet/i);
        fireEvent.click(webCheckbox);

        expect(useReportStore.getState().filterTypes.web).toBe(false);
    });
});
