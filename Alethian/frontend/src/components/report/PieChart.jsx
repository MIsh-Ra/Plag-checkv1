import { PieChart as RechartsPieChart, Pie, Tooltip, Cell, Legend, ResponsiveContainer } from 'recharts';

// Monochromatic Forensic Lab Palette (strict grayscale + single error tint)
const COLORS = ['#e2e2e2', '#c6c6c6', '#5d5f5f', '#353535', '#ffb4ab'];

export default function PieChart({ data }) {
    if (!data || data.length === 0) return <div className="text-on-surface-variant text-xs font-mono tracking-widest italic">NO DATA AVAILABLE.</div>;

    return (
        <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                    <Pie 
                        data={data} 
                        dataKey="value" 
                        nameKey="name" 
                        cx="50%" 
                        cy="50%" 
                        innerRadius={50} 
                        outerRadius={70} 
                        stroke="#131313" 
                        strokeWidth={2}
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip 
                        contentStyle={{ backgroundColor: '#1b1b1b', borderColor: '#474747', borderRadius: '0px', color: '#e2e2e2' }} 
                        itemStyle={{ color: '#ffffff' }}
                    />
                </RechartsPieChart>
            </ResponsiveContainer>
        </div>
    );
}
