import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Tabs } from '@/components/Tabs';
import { Badge } from '@/components/Badge';
import type { InterviewPlan } from '@/lib/types';
import { Clock, AlertCircle } from 'lucide-react';

interface InterviewPlanSectionProps {
  plan: InterviewPlan;
}

export function InterviewPlanSection({ plan }: InterviewPlanSectionProps) {
  // Handle undefined/null interviewers array
  if (!plan || !plan.interviewers || plan.interviewers.length === 0) {
    return null;
  }

  const tabs = plan.interviewers.map((interviewer) => ({
    id: interviewer.interviewer_role,
    label: `${interviewer.interviewer_role} (${interviewer.time_estimate_minutes}m)`,
    content: (
      <div className="space-y-4">
        {/* Priority Areas */}
        {interviewer.priority_areas && interviewer.priority_areas.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">Priority Areas</h4>
            <div className="flex flex-wrap gap-2">
              {interviewer.priority_areas.map((area, idx) => (
                <Badge key={idx} variant="info">
                  {area}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Questions */}
        <div className="space-y-4">
          {interviewer.questions && interviewer.questions.map((question, idx) => (
            <div key={idx} className="border border-gray-200 rounded-lg p-4 bg-white">
              <div className="flex items-start gap-3 mb-3">
                <div className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-semibold">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{question.question_text}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    Category: {question.category_probed}
                  </p>
                </div>
              </div>

              {/* What to Listen For */}
              {question.what_to_listen_for && question.what_to_listen_for.length > 0 && (
                <div className="mb-3">
                  <h5 className="text-sm font-semibold text-gray-700 mb-1">
                    What to Listen For:
                  </h5>
                  <ul className="space-y-1">
                    {question.what_to_listen_for.map((item, itemIdx) => (
                      <li key={itemIdx} className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-green-500 mt-1.5" />
                        <span className="text-gray-700">{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Red Flags */}
              {question.red_flags && question.red_flags.length > 0 && (
                <div className="mb-3 bg-red-50 border border-red-200 rounded p-3">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="h-4 w-4 text-red-600" />
                    <h5 className="text-sm font-semibold text-red-900">Red Flags:</h5>
                  </div>
                  <ul className="space-y-1">
                    {question.red_flags.map((flag, flagIdx) => (
                      <li key={flagIdx} className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5" />
                        <span className="text-red-800">{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Follow-up Prompts */}
              {question.follow_up_prompts && question.follow_up_prompts.length > 0 && (
                <div>
                  <h5 className="text-sm font-semibold text-gray-700 mb-1">
                    Follow-up Prompts:
                  </h5>
                  <ul className="space-y-1">
                    {question.follow_up_prompts.map((prompt, promptIdx) => (
                      <li key={promptIdx} className="flex items-start gap-2 text-sm">
                        <span className="flex-shrink-0 text-primary-600">→</span>
                        <span className="text-gray-700">{prompt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    ),
  }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Interview Plan</CardTitle>
        <div className="flex items-center gap-4 mt-2 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            <span>Total Time: {plan.total_time_estimate_minutes} minutes</span>
          </div>
        </div>
        {plan.overall_focus && (
          <p className="text-gray-700 mt-2">
            <strong>Overall Focus:</strong> {plan.overall_focus}
          </p>
        )}
      </CardHeader>
      <CardContent>
        <Tabs tabs={tabs} />
      </CardContent>
    </Card>
  );
}
