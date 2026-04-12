import { CheckCircle } from 'lucide-react';

export default function ScoreHeader({ score }) {
    const riskLevel = score < 50 ? 'high' : score < 80 ? 'moderate' : 'low';

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 flex flex-col items-center justify-center">
            <h2 className="text-sm font-medium text-gray-500 uppercase tracking-wider mb-2">Originality Score</h2>
            <div className="flex items-baseline space-x-2">
                <span className={`text-5xl font-extrabold ${riskLevel === 'high' ? 'text-red-600' : riskLevel === 'moderate' ? 'text-yellow-500' : 'text-green-600'}`}>
                    {Math.round(score)}%
                </span>
            </div>
            
            <div className="mt-4 flex items-center space-x-2">
                {riskLevel === 'high' && <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">🔴 High Risk</span>}
                {riskLevel === 'moderate' && <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">🟡 Moderate Risk</span>}
                {riskLevel === 'low' && <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"><CheckCircle className="w-3 h-3 mr-1"/> Low Risk</span>}
            </div>
        </div>
    );
}
