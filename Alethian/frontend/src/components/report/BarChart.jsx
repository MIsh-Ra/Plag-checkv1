import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
export default function BarChart({ data }) {
    return (
        <RechartsBarChart width={150} height={40} data={data || []}>
            <Bar dataKey="density_score" fill="#8884d8" />
            <XAxis dataKey="page_number" />
            <YAxis />
            <Tooltip />
        </RechartsBarChart>
    );
}
