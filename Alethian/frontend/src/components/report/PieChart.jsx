import { PieChart as RechartsPieChart, Pie, Tooltip, Cell, Legend, ResponsiveContainer } from 'recharts';

const COLORS = ['#ef4444', '#f97316', '#3b82f6', '#22c55e', '#8b5cf6'];

export default function PieChart({ data }) {
    if (!data || data.length === 0) return <div className="text-gray-400 text-sm italic">No data available.</div>;

    return (
        <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
                <RechartsPieChart>
                    <Pie 
                        data={data} 
                        dataKey="value" 
                        nameKey="name" 
                        cx="50%" 
                        cy="50%" 
                        innerRadius={40} 
                        outerRadius={80} 
                        label 
                    >
                        {data.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                    </Pie>
                    <Tooltip />
                    <Legend verticalAlign="bottom" height={36}/>
                </RechartsPieChart>
            </ResponsiveContainer>
        </div>
    );
}
