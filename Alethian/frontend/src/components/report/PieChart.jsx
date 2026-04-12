import { PieChart as RechartsPieChart, Pie, Tooltip } from 'recharts';
export default function PieChart({ data }) {
    return (
        <RechartsPieChart width={400} height={400}>
            <Pie dataKey="value" isAnimationActive={false} data={data || []} cx="50%" cy="50%" outerRadius={80} fill="#8884d8" label />
            <Tooltip />
        </RechartsPieChart>
    );
}
