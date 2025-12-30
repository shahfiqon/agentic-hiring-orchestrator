import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Accordion } from '@/components/Accordion';
import { Badge } from '@/components/Badge';
import type { Rubric } from '@/lib/types';

interface RubricDisplayProps {
  rubric: Rubric;
}

export function RubricDisplay({ rubric }: RubricDisplayProps) {
  // Handle undefined/null categories array
  if (!rubric || !rubric.categories || rubric.categories.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Evaluation Rubric</CardTitle>
        <p className="text-gray-600 mt-1">
          Role: <span className="font-semibold">{rubric.role_title}</span>
        </p>
      </CardHeader>
      <CardContent>
        <Accordion
          items={rubric.categories.map((category) => ({
            title: (
              <div className="flex items-center justify-between w-full">
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{category.name}</span>
                  {category.must_have && (
                    <Badge variant="danger">Must-Have</Badge>
                  )}
                </div>
                <span className="text-sm text-gray-600">
                  Weight: {(category.weight * 100).toFixed(0)}%
                </span>
              </div>
            ) as any,
            content: (
              <div className="space-y-4">
                <p className="text-gray-700">{category.description}</p>
                <div>
                  <h5 className="font-semibold text-gray-900 mb-3">Scoring Criteria</h5>
                  <div className="space-y-2">
                    {category.scoring_criteria
                      .sort((a, b) => b.score - a.score)
                      .map((criteria, idx) => (
                        <div
                          key={idx}
                          className="flex gap-3 p-3 bg-gray-50 rounded-lg"
                        >
                          <div className="flex-shrink-0">
                            <div className="flex items-center justify-center w-10 h-10 rounded-full bg-primary-100 text-primary-700 font-bold">
                              {criteria.score}
                            </div>
                          </div>
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 mb-1">
                              {criteria.label}
                            </div>
                            <div className="text-sm text-gray-600">
                              {criteria.description}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            ),
          }))}
        />
      </CardContent>
    </Card>
  );
}
