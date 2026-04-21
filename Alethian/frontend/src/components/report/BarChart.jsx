import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useReportStore } from '../../stores/reportStore';

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-surface-container-highest border border-ghost p-3 shadow-ambient text-[10px] font-mono uppercase tracking-widest">
                <p className="text-on-surface font-bold mb-1">PAGE {label}</p>
                {payload.map((entry) => (
                    entry.value > 0 && (
                        <p key={entry.name} style={{ color: entry.fill }} className="text-[10px]">
                            {entry.name}: {entry.value}
                        </p>
                    )
                ))}
            </div>
        );
    }
    return null;
};

export default function BarChart({ data }) {
    const { setCurrentPage } = useReportStore();

    const handleBarClick = (chartData) => {
        if (chartData && chartData.activePayload && chartData.activePayload.length > 0) {
            const pageNum = chartData.activePayload[0]?.payload?.page;
            if (pageNum) setCurrentPage(pageNum);
        }
    };

    return (
        <div className="h-40 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart
                    data={data || []}
                    barGap={1}
                    barCategoryGap={2}
                    onClick={handleBarClick}
                    style={{ cursor: 'pointer' }}
                >
                    {/* Stacked bars by match type per Report_Design_v2 spec */}
                    <Bar dataKey="internal_exact" stackId="a" name="EXACT" fill="#ef4444" radius={0} />
                    <Bar dataKey="internal_paraphrase" stackId="a" name="PARAPHRASE" fill="#f97316" radius={0} />
                    <Bar dataKey="web" stackId="a" name="WEB" fill="#e2e2e2" radius={0} />
                    <XAxis
                        dataKey="page"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#c6c6c6', fontSize: 9, fontFamily: 'monospace', textTransform: 'uppercase' }}
                        interval="preserveStartEnd"
                    />
                    <YAxis hide={true} />
                    <Tooltip
                        content={<CustomTooltip />}
                        cursor={{ fill: '#2a2a2a' }}
                    />
                </RechartsBarChart>
            </ResponsiveContainer>
        </div>
    );
}
