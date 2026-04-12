import { useReportStore } from '../../stores/reportStore';

export default function TextOverlay({ text }) {
    const { currentPage } = useReportStore();

    return (
        <div className="relative font-serif text-lg leading-loose text-gray-800 bg-white p-12 pr-24 border border-gray-100 rounded-md shadow-inner min-h-[800px]">
            <div className="absolute top-4 right-4 text-xs font-bold text-gray-400">PAGE {currentPage}</div>
            
            {/* For now, just rendering the raw text. A full implementation would parse exact ranges to wrap spans around them. */}
            {text.split('\n').map((paragraph, idx) => {
                if (!paragraph.trim()) return <br key={idx} />;
                
                // Demo highlight: ideally this highlights matching ranges found in matches list
                // Since text is dummy, we will demonstrate a dummy UI logic here
                return (
                    <p key={idx} className="mb-4">
                        {paragraph}
                    </p>
                );
            })}
        </div>
    );
}
