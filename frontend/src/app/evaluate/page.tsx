'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Container } from '@/components/Container';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/Card';
import { Button } from '@/components/Button';
import { Alert } from '@/components/Alert';
import { evaluationSchema, type EvaluationFormData } from '@/lib/validation';
import { FileText, Upload, Download, ArrowLeft, Loader2 } from 'lucide-react';
import type { ApiError, EvaluationResponse, JobStatus } from '@/lib/types';
import { DecisionSummary } from '@/components/results/DecisionSummary';
import { RubricDisplay } from '@/components/results/RubricDisplay';
import { AgentReviews } from '@/components/results/AgentReviews';
import { DisagreementSection } from '@/components/results/DisagreementSection';
import { InterviewPlanSection } from '@/components/results/InterviewPlanSection';

export default function EvaluatePage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [results, setResults] = useState<EvaluationResponse | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [progress, setProgress] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    setValue,
  } = useForm<EvaluationFormData>({
    resolver: zodResolver(evaluationSchema),
    defaultValues: {
      job_description: '',
      resume: '',
      company_context: '',
    },
  });

  const onSubmit = async (data: EvaluationFormData) => {
    setIsSubmitting(true);
    setApiError(null);
    setJobStatus('pending');
    setProgress('Submitting evaluation request...');

    try {
      // Submit evaluation job
      const response = await fetch('/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw {
          message: errorData.error || 'Evaluation submission failed',
          status: response.status,
          details: errorData,
        };
      }

      const submissionResult = await response.json();
      const jobId = submissionResult.job_id;

      // Start polling for job status
      setProgress('Evaluation in progress...');
      await pollJobStatus(jobId);
    } catch (error: any) {
      setApiError(error);
      setIsSubmitting(false);
      setJobStatus(null);
      setProgress('');
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const maxAttempts = 300; // 10 minutes with 2 second intervals
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await fetch(`/api/evaluate?job_id=${jobId}`);

        if (!response.ok) {
          throw new Error('Failed to fetch job status');
        }

        const statusData = await response.json();

        // Update status and progress
        setJobStatus(statusData.status);
        if (statusData.progress) {
          setProgress(statusData.progress);
        }

        // Check if completed
        if (statusData.status === 'completed') {
          setResults(statusData.result);
          setIsSubmitting(false);
          setJobStatus(null);
          setProgress('');
          return;
        }

        // Check if failed
        if (statusData.status === 'failed') {
          throw {
            message: statusData.error || 'Evaluation failed',
            status: 500,
            details: statusData,
          };
        }

        // Continue polling if still processing
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 2000); // Poll every 2 seconds
        } else {
          throw {
            message: 'Evaluation timeout: Maximum wait time exceeded',
            status: 408,
            details: { jobId },
          };
        }
      } catch (error: any) {
        setApiError(error);
        setIsSubmitting(false);
        setJobStatus(null);
        setProgress('');
      }
    };

    // Start polling
    poll();
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setValue('resume', text, { shouldValidate: true });
    };
    reader.readAsText(file);
  };

  const handleExportJSON = () => {
    if (!results) return;

    const dataStr = JSON.stringify(results, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `evaluation-results-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleNewEvaluation = () => {
    setResults(null);
    setApiError(null);
    setJobStatus(null);
    setProgress('');
  };

  // If results exist, show the results view
  if (results) {
    return (
      <div className="bg-gray-50 py-12">
        <Container size="xl">
          {/* Header Actions */}
          <div className="flex items-center justify-between mb-8">
            <Button variant="ghost" onClick={handleNewEvaluation}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              New Evaluation
            </Button>
            <Button variant="secondary" onClick={handleExportJSON}>
              <Download className="mr-2 h-4 w-4" />
              Export Results (JSON)
            </Button>
          </div>

          {/* Results Content */}
          <div className="space-y-8">
            {/* Decision Summary */}
            {results.decision_packet && (
              <DecisionSummary packet={results.decision_packet} />
            )}

            {/* Rubric */}
            {results.rubric && (
              <RubricDisplay rubric={results.rubric} />
            )}

            {/* Agent Reviews */}
            {results.agent_reviews && (
              <AgentReviews
                reviews={results.agent_reviews}
                workingMemories={results.working_memories}
              />
            )}

            {/* Disagreements */}
            {results.decision_packet?.disagreements && (
              <DisagreementSection disagreements={results.decision_packet.disagreements} />
            )}

            {/* Interview Plan */}
            {results.interview_plan && (
              <InterviewPlanSection plan={results.interview_plan} />
            )}

            {/* Metadata */}
            {results.metadata && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Evaluation Metadata</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Workflow ID:</span>
                    <p className="font-mono text-xs text-gray-900 mt-1">
                      {results.metadata.workflow_id}
                    </p>
                  </div>
                  {results.metadata.total_duration_seconds && (
                    <div>
                      <span className="text-gray-600">Duration:</span>
                      <p className="text-gray-900 mt-1">
                        {Math.round(results.metadata.total_duration_seconds)}s
                      </p>
                    </div>
                  )}
                  {results.metadata.started_at && (
                    <div>
                      <span className="text-gray-600">Started:</span>
                      <p className="text-gray-900 mt-1">
                        {new Date(results.metadata.started_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                  {results.metadata.completed_at && (
                    <div>
                      <span className="text-gray-600">Completed:</span>
                      <p className="text-gray-900 mt-1">
                        {new Date(results.metadata.completed_at).toLocaleString()}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-center gap-4 mt-12 pt-8 border-t border-gray-200">
            <Button size="lg" onClick={handleNewEvaluation}>
              <ArrowLeft className="mr-2 h-5 w-5" />
              Evaluate Another Candidate
            </Button>
            <Button size="lg" variant="secondary" onClick={handleExportJSON}>
              <Download className="mr-2 h-5 w-5" />
              Export Results
            </Button>
          </div>
        </Container>
      </div>
    );
  }

  // Otherwise, show the form view
  return (
    <div className="bg-gray-50 py-12">
      <Container size="md">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <FileText className="h-8 w-8 text-primary-600" />
              <CardTitle className="text-2xl">Start Candidate Evaluation</CardTitle>
            </div>
            <p className="text-gray-600">
              Submit a job description and resume to begin a comprehensive multi-agent evaluation.
              This process typically takes 1-2 minutes.
            </p>
          </CardHeader>
          <CardContent>
            {apiError && (
              <Alert variant="error" className="mb-6">
                <strong>Error:</strong> {apiError.message}
                {apiError.details && (
                  <pre className="mt-2 text-xs overflow-auto">
                    {JSON.stringify(apiError.details, null, 2)}
                  </pre>
                )}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Job Description */}
              <div>
                <label
                  htmlFor="job_description"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Job Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  id="job_description"
                  rows={8}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="Paste the full job description here..."
                  {...register('job_description')}
                />
                {errors.job_description && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.job_description.message}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Minimum 50 characters, maximum 10,000 characters
                </p>
              </div>

              {/* Resume */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label
                    htmlFor="resume"
                    className="block text-sm font-medium text-gray-700"
                  >
                    Resume <span className="text-red-500">*</span>
                  </label>
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept=".txt,.md"
                      className="hidden"
                      onChange={handleFileUpload}
                    />
                    <span className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700">
                      <Upload className="h-4 w-4" />
                      Upload from file
                    </span>
                  </label>
                </div>
                <textarea
                  id="resume"
                  rows={12}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="Paste the candidate's resume here or upload a text file..."
                  {...register('resume')}
                />
                {errors.resume && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.resume.message}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Paste the candidate's complete resume
                </p>
              </div>

              {/* Company Context (Optional) */}
              <div>
                <label
                  htmlFor="company_context"
                  className="block text-sm font-medium text-gray-700 mb-2"
                >
                  Company Context <span className="text-gray-400">(Optional)</span>
                </label>
                <textarea
                  id="company_context"
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-colors"
                  placeholder="Additional company or role context to help agents understand the evaluation criteria..."
                  {...register('company_context')}
                />
                {errors.company_context && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.company_context.message}
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500">
                  Maximum 5,000 characters
                </p>
              </div>

              {/* Submit Button */}
              <div className="pt-4 border-t border-gray-200">
                {isSubmitting && progress && (
                  <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-blue-900">
                          {jobStatus === 'pending' && 'Queued for processing...'}
                          {jobStatus === 'processing' && 'Processing evaluation...'}
                        </p>
                        <p className="text-xs text-blue-700 mt-1">{progress}</p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
                    {isSubmitting
                      ? 'Evaluation in progress... This may take several minutes.'
                      : 'Ready to submit? Click the button to start the evaluation.'}
                  </p>
                  <Button
                    type="submit"
                    size="lg"
                    loading={isSubmitting}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Evaluating...' : 'Start Evaluation'}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>
      </Container>
    </div>
  );
}
