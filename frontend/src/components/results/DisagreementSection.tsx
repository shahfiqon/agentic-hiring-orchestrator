import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import type { Disagreement } from '@/lib/types';
import { AlertTriangle } from 'lucide-react';

interface DisagreementSectionProps {
  disagreements: Disagreement[];
}

export function DisagreementSection({ disagreements }: DisagreementSectionProps) {
  if (!disagreements || disagreements.length === 0) {
    return null;
  }

  return (
    <Card className="border-orange-200 bg-orange-50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-orange-600" />
          <CardTitle className="text-2xl">Agent Disagreements</CardTitle>
        </div>
        <p className="text-gray-600 mt-1">
          The following categories had significant disagreements between agents
        </p>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {disagreements.map((disagreement, idx) => (
            <div key={idx} className="bg-white border border-orange-200 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 mb-3">
                {disagreement.category_name}
              </h4>

              {/* Agent Scores Comparison */}
              <div className="mb-3">
                <h5 className="text-sm font-semibold text-gray-700 mb-2">
                  Agent Scores:
                </h5>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(disagreement.agent_scores).map(([agent, score]) => (
                    <div
                      key={agent}
                      className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded border border-gray-300"
                    >
                      <span className="text-sm text-gray-700">{agent}:</span>
                      <span className="text-lg font-bold text-gray-900">
                        {score.toFixed(1)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Visual Score Comparison */}
              <div className="mb-3">
                <div className="flex items-center gap-2 h-8">
                  {Object.entries(disagreement.agent_scores).map(([agent, score]) => (
                    <div key={agent} className="flex-1">
                      <div className="relative h-8 bg-gray-200 rounded">
                        <div
                          className="absolute h-full bg-primary-600 rounded"
                          style={{ width: `${(score / 5) * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Reason */}
              <div className="mb-3">
                <h5 className="text-sm font-semibold text-gray-700 mb-1">
                  Reason for Disagreement:
                </h5>
                <div 
                  className="text-gray-700 whitespace-pre-wrap" 
                  dangerouslySetInnerHTML={{ __html: disagreement.reason }} 
                />
              </div>

              {/* Resolution */}
              <div>
                <h5 className="text-sm font-semibold text-gray-700 mb-1">
                  Resolution Approach:
                </h5>
                <div 
                  className="text-gray-700 whitespace-pre-wrap" 
                  dangerouslySetInnerHTML={{ __html: disagreement.resolution_approach }} 
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
