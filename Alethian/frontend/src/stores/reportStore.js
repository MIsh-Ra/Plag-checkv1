import { create } from 'zustand';

export const useReportStore = create((set, get) => ({
    selectedMatchId: null,
    selectedSourceId: null,
    currentPage: 1,
    filterTypes: {
        internal_exact: true,
        internal_paraphrase: true,
        web: true,
        excluded: false
    },
    
    setSelectedMatch: (id) => set({ selectedMatchId: id }),
    setSelectedSource: (id) => set({ selectedSourceId: id }),
    setCurrentPage: (n) => set({ currentPage: n }),
    toggleFilterType: (type) => set((state) => ({
        filterTypes: {
            ...state.filterTypes,
            [type]: !state.filterTypes[type]
        }
    }))
}));
