'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Container } from '@/components/Container';
import { Button } from '@/components/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Badge } from '@/components/Badge';
import { Alert } from '@/components/Alert';
import { getHealth } from '@/lib/api';
import type { HealthResponse } from '@/lib/types';
import { Brain, Users, FileCheck, GitBranch, ArrowRight } from 'lucide-react';

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await getHealth();
        setHealth(response);
        setHealthError(null);
      } catch (error: any) {
        setHealthError(error.message || 'Failed to connect to backend');
      }
    };

    checkHealth();
  }, []);

  return (
    <div className="bg-gray-50">
      <Container className="py-12">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <Brain className="h-20 w-20 text-primary-600" />
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Agentic Hiring Orchestrator
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            AI-powered multi-agent system for comprehensive, evidence-based hiring evaluations.
            Orchestrates HR, Technical, and Compliance agents to provide structured,
            rubric-driven candidate assessments.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/evaluate">
              <Button size="lg">
                Start Evaluation
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            {health && (
              <Badge variant="success">
                Backend: {health.status}
              </Badge>
            )}
            {healthError && (
              <Badge variant="danger">
                Backend: Offline
              </Badge>
            )}
          </div>
        </div>

        {/* Backend Status */}
        {healthError && (
          <Alert variant="error" className="mb-12">
            <strong>Backend Connection Error:</strong> {healthError}
            <br />
            Make sure the backend server is running at{' '}
            <code className="bg-red-100 px-1 rounded">
              {process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}
            </code>
          </Alert>
        )}

        {/* Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <Users className="h-6 w-6 text-primary-600" />
                <CardTitle>Multi-Agent System</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                HR, Technical, and Compliance agents work together to evaluate
                candidates from different perspectives.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <FileCheck className="h-6 w-6 text-primary-600" />
                <CardTitle>Evidence-Based</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Every score is backed by specific evidence from the resume,
                with quotes and detailed interpretations.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <GitBranch className="h-6 w-6 text-primary-600" />
                <CardTitle>Two-Pass Workflow</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                First pass extracts working memory, second pass performs
                rubric-based scoring for thorough evaluation.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <Brain className="h-6 w-6 text-primary-600" />
                <CardTitle>Interview Planning</CardTitle>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Automatically generates structured interview questions with
                follow-ups and red flags to watch for.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* How It Works */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="text-2xl">How It Works</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4">
              <li className="flex gap-4">
                <span className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-semibold">
                  1
                </span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Submit Job Description and Resume
                  </h3>
                  <p className="text-gray-600">
                    Provide the job description, candidate resume, and optional company
                    context to start the evaluation process.
                  </p>
                </div>
              </li>
              <li className="flex gap-4">
                <span className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-semibold">
                  2
                </span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Rubric Generation
                  </h3>
                  <p className="text-gray-600">
                    The orchestrator analyzes the job description to create a structured
                    rubric with weighted categories and scoring criteria.
                  </p>
                </div>
              </li>
              <li className="flex gap-4">
                <span className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-semibold">
                  3
                </span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Multi-Agent Evaluation
                  </h3>
                  <p className="text-gray-600">
                    HR, Tech, and Compliance agents independently evaluate the candidate,
                    building working memory and scoring against the rubric.
                  </p>
                </div>
              </li>
              <li className="flex gap-4">
                <span className="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full bg-primary-100 text-primary-700 font-semibold">
                  4
                </span>
                <div>
                  <h3 className="font-semibold text-gray-900 mb-1">
                    Results and Interview Plan
                  </h3>
                  <p className="text-gray-600">
                    Receive a comprehensive decision packet with scores, disagreement
                    analysis, and a structured interview plan.
                  </p>
                </div>
              </li>
            </ol>
          </CardContent>
        </Card>

        {/* CTA */}
        <div className="text-center">
          <Link href="/evaluate">
            <Button size="lg">
              Get Started with Your First Evaluation
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </Container>
    </div>
  );
}
