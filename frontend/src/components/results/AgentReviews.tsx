import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Tabs } from '@/components/Tabs';
import { Accordion } from '@/components/Accordion';
import type { AgentReview, WorkingMemory } from '@/lib/types';
import { getScoreColor, getScoreBgColor } from '@/lib/utils';
import { User, Laptop, Shield } from 'lucide-react';

interface AgentReviewsProps {
  reviews: AgentReview[];
  workingMemories?: WorkingMemory[];
}

export function AgentReviews({ reviews, workingMemories }: AgentReviewsProps) {
  // Handle undefined/null reviews array
  if (!reviews || reviews.length === 0) {
    return null;
  }

  const getAgentIcon = (agentName: string) => {
    if (agentName.toLowerCase().includes('hr')) return User;
    if (agentName.toLowerCase().includes('tech')) return Laptop;
    if (agentName.toLowerCase().includes('compliance')) return Shield;
    return User;
  };

  const tabs = reviews.map((review) => {
    const Icon = getAgentIcon(review.agent_name);
    const agentMemory = workingMemories?.find(
      (m) => m.agent_name === review.agent_name
    );

    return {
      id: review.agent_name,
      label: (
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4" />
          {review.agent_name}
        </div>
      ) as any,
      content: (
        <div className="space-y-6">
          {/* Overall Assessment */}
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Overall Assessment</h4>
            <p className="text-gray-700 whitespace-pre-wrap">
              {review.overall_assessment}
            </p>
          </div>

          {/* Category Scores */}
          {review.category_scores && review.category_scores.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-3">Category Scores</h4>
              <div className="space-y-3">
                {review.category_scores.map((score, idx) => (
                <div
                  key={idx}
                  className={`border rounded-lg p-4 ${getScoreBgColor(score.score)}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <h5 className="font-semibold text-gray-900">
                      {score.category_name}
                    </h5>
                    <span className={`text-2xl font-bold ${getScoreColor(score.score)}`}>
                      {score.score.toFixed(1)}
                    </span>
                  </div>
                  <p className="text-gray-700 mb-3">{score.rationale}</p>

                  {/* Evidence */}
                  {score.evidence && score.evidence.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-300">
                      <h6 className="text-sm font-semibold text-gray-900 mb-2">
                        Evidence:
                      </h6>
                      <div className="space-y-2">
                        {score.evidence.map((ev, evIdx) => (
                          <div key={evIdx} className="text-sm">
                            <div className="bg-white bg-opacity-60 p-2 rounded border border-gray-300 mb-1">
                              <span className="text-gray-600 italic">"{ev.resume_text}"</span>
                              <span className="text-xs text-gray-500 ml-2">
                                ({ev.line_reference})
                              </span>
                            </div>
                            <p className="text-gray-700 ml-2">{ev.interpretation}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              </div>
            </div>
          )}

          {/* Strengths and Risks */}
          <div className="grid md:grid-cols-2 gap-4">
            {review.top_strengths && review.top_strengths.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Top Strengths</h4>
                <ul className="space-y-1">
                  {review.top_strengths.map((strength, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5" />
                      <span className="text-gray-700">{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {review.top_risks && review.top_risks.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Top Risks</h4>
                <ul className="space-y-1">
                  {review.top_risks.map((risk, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-orange-500 mt-1.5" />
                      <span className="text-gray-700">{risk}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Follow-up Questions */}
          {review.follow_up_questions && review.follow_up_questions.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Follow-up Questions</h4>
              <ul className="space-y-1">
                {review.follow_up_questions.map((question, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <span className="flex-shrink-0 text-primary-600 font-semibold">
                      {idx + 1}.
                    </span>
                    <span className="text-gray-700">{question}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Working Memory */}
          {agentMemory && (
            <Accordion
              items={[
                {
                  title: 'Working Memory (Click to expand)',
                  content: (
                    <div className="space-y-4">
                      <div>
                        <h5 className="font-semibold text-gray-900 mb-2">
                          Key Observations
                        </h5>
                        {agentMemory.key_observations && agentMemory.key_observations.map((obs, idx) => (
                          <div key={idx} className="mb-3 p-3 bg-gray-50 rounded">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-gray-900">
                                {obs.observation_text}
                              </span>
                              <span
                                className={`text-xs px-2 py-0.5 rounded ${
                                  obs.importance === 'critical'
                                    ? 'bg-red-100 text-red-800'
                                    : obs.importance === 'moderate'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}
                              >
                              {obs.importance}
                            </span>
                          </div>
                          {obs.cross_references && obs.cross_references.length > 0 && (
                            <div className="text-xs text-gray-600 mt-2">
                              <strong>Cross-references:</strong>
                              {obs.cross_references.map((ref, refIdx) => (
                                <div key={refIdx} className="ml-2 mt-1">
                                  {ref.resume_section} ↔ {ref.jd_requirement} (
                                  {ref.alignment_type})
                                </div>
                              ))}
                            </div>
                          )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ),
                },
              ]}
            />
          )}
        </div>
      ),
    };
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Agent Reviews</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs tabs={tabs} />
      </CardContent>
    </Card>
  );
}
