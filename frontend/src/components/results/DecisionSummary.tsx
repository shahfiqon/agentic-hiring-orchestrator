import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { ProgressBar } from '@/components/ProgressBar';
import type { DecisionPacket } from '@/lib/types';
import {
  getConfidenceColor,
  getRecommendationColor,
  formatRecommendation,
  calculatePercentage,
} from '@/lib/utils';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';

interface DecisionSummaryProps {
  packet: DecisionPacket;
}

export function DecisionSummary({ packet }: DecisionSummaryProps) {
  const scorePercentage = calculatePercentage(packet.overall_fit_score, 5);

  let scoreColor: 'primary' | 'success' | 'warning' | 'danger' = 'primary';
  if (packet.overall_fit_score >= 4) scoreColor = 'success';
  else if (packet.overall_fit_score >= 3) scoreColor = 'warning';
  else if (packet.overall_fit_score < 2) scoreColor = 'danger';

  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="text-2xl">Decision Summary</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Score Display */}
        <div>
          <div className="flex items-end gap-4 mb-3">
            <div className="text-5xl font-bold text-gray-900">
              {packet.overall_fit_score.toFixed(1)}
              <span className="text-2xl text-gray-500">/5.0</span>
            </div>
            <div className="flex gap-2 mb-2">
              <Badge className={getRecommendationColor(packet.recommendation)}>
                {formatRecommendation(packet.recommendation)}
              </Badge>
              <Badge className={getConfidenceColor(packet.confidence_level)}>
                {packet.confidence_level.toUpperCase()} Confidence
              </Badge>
            </div>
          </div>
          <ProgressBar value={packet.overall_fit_score} max={5} color={scoreColor} />
        </div>

        {/* Strengths */}
        {packet.top_strengths && packet.top_strengths.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <h4 className="font-semibold text-gray-900">Top Strengths</h4>
            </div>
            <ul className="space-y-2">
              {packet.top_strengths.map((strength, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-green-500 mt-2" />
                  <span className="text-gray-700">{strength}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Risks */}
        {packet.top_risks && packet.top_risks.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingDown className="h-5 w-5 text-orange-600" />
              <h4 className="font-semibold text-gray-900">Top Risks</h4>
            </div>
            <ul className="space-y-2">
              {packet.top_risks.map((risk, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-orange-500 mt-2" />
                  <span className="text-gray-700">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Must-Have Gaps */}
        {packet.must_have_gaps && packet.must_have_gaps.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-5 w-5 text-red-600" />
              <h4 className="font-semibold text-red-900">Must-Have Gaps</h4>
            </div>
            <ul className="space-y-2">
              {packet.must_have_gaps.map((gap, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-red-500 mt-2" />
                  <span className="text-red-800">{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Synthesis Notes */}
        {packet.synthesis_notes && (
          <div className="pt-4 border-t border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-2">Synthesis Notes</h4>
            <p className="text-gray-700 whitespace-pre-wrap">{packet.synthesis_notes}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
