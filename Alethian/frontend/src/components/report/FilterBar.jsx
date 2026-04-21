import { useReportStore } from '../../stores/reportStore';

export default function FilterBar() {
    const { filterTypes, toggleFilterType } = useReportStore();

    return (
        <div className="flex flex-col space-y-4">
            <h3 className="text-[10px] font-bold uppercase tracking-widest text-on-surface">Filter Vectors</h3>
            <div className="space-y-3">
                <label className="flex items-center cursor-pointer group">
                    <input 
                        type="checkbox" 
                        checked={filterTypes.internal_exact} 
                        onChange={() => toggleFilterType('internal_exact')} 
                        className="sr-only"
                    />
                    <div className={`w-4 h-4 border flex items-center justify-center transition-colors ${filterTypes.internal_exact ? 'bg-error border-error shadow-ambient' : 'border-ghost bg-surface-container-highest group-hover:border-error/50'}`}>
                        {filterTypes.internal_exact && <div className="w-1.5 h-1.5 bg-on-error" />}
                    </div>
                    <span className="ml-3 text-xs font-mono tracking-wide text-on-surface-variant group-hover:text-on-surface transition-colors uppercase">Archival Exact</span>
                    <span className="ml-auto w-1.5 h-1.5 bg-error"></span>
                </label>

                <label className="flex items-center cursor-pointer group">
                    <input 
                        type="checkbox" 
                        checked={filterTypes.internal_paraphrase} 
                        onChange={() => toggleFilterType('internal_paraphrase')} 
                        className="sr-only"
                    />
                    <div className={`w-4 h-4 border flex items-center justify-center transition-colors ${filterTypes.internal_paraphrase ? 'bg-tertiary-container border-tertiary-container shadow-ambient' : 'border-ghost bg-surface-container-highest group-hover:border-tertiary-container/50'}`}>
                        {filterTypes.internal_paraphrase && <div className="w-1.5 h-1.5 bg-on-tertiary-container" />}
                    </div>
                    <span className="ml-3 text-xs font-mono tracking-wide text-on-surface-variant group-hover:text-on-surface transition-colors uppercase">Archival Paraphrase</span>
                    <span className="ml-auto w-1.5 h-1.5 bg-tertiary-container"></span>
                </label>

                <label className="flex items-center cursor-pointer group">
                    <input 
                        type="checkbox" 
                        checked={filterTypes.web} 
                        onChange={() => toggleFilterType('web')} 
                        className="sr-only"
                    />
                    <div className={`w-4 h-4 border flex items-center justify-center transition-colors ${filterTypes.web ? 'bg-primary border-primary shadow-ambient' : 'border-ghost bg-surface-container-highest group-hover:border-primary/50'}`}>
                        {filterTypes.web && <div className="w-1.5 h-1.5 bg-on-primary" />}
                    </div>
                    <span className="ml-3 text-xs font-mono tracking-wide text-on-surface-variant group-hover:text-on-surface transition-colors uppercase">Web Dragnet</span>
                    <span className="ml-auto w-1.5 h-1.5 bg-primary"></span>
                </label>

                <div className="pt-2 border-t border-ghost">
                    <label className="flex items-center cursor-pointer group">
                        <input 
                            type="checkbox" 
                            checked={filterTypes.excluded} 
                            onChange={() => toggleFilterType('excluded')} 
                            className="sr-only"
                        />
                        <div className={`w-4 h-4 border flex items-center justify-center transition-colors ${filterTypes.excluded ? 'bg-on-surface-variant border-on-surface-variant' : 'border-ghost bg-surface-container-highest group-hover:border-on-surface-variant/50'}`}>
                            {filterTypes.excluded && <div className="w-1.5 h-1.5 bg-surface" />}
                        </div>
                        <span className="ml-3 text-xs font-mono tracking-wide text-on-surface-variant group-hover:text-on-surface transition-colors uppercase italic opacity-70">Show Excluded</span>
                        <span className="ml-auto w-1.5 h-1.5 bg-surface-container-highest border border-ghost"></span>
                    </label>
                </div>
            </div>
        </div>
    );
}
