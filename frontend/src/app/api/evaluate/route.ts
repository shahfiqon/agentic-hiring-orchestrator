import { NextRequest, NextResponse } from 'next/server';
import { submitEvaluation, getJobStatus } from '@/lib/api';
import type { EvaluationRequest } from '@/lib/types';

export async function POST(request: NextRequest) {
  try {
    // Parse request body
    const body: EvaluationRequest = await request.json();

    // Validate required fields
    if (!body.job_description || !body.resume) {
      return NextResponse.json(
        { error: 'Missing required fields: job_description and resume are required' },
        { status: 400 }
      );
    }

    // Submit evaluation job (returns job ID)
    const result = await submitEvaluation(body);

    // Return job submission response
    return NextResponse.json(result, { status: 202 });
  } catch (error: any) {
    console.error('API route error:', error);

    // Handle different error types
    if (error.status) {
      return NextResponse.json(
        {
          error: error.message || 'Evaluation submission failed',
          details: error.details,
        },
        { status: error.status }
      );
    }

    // Generic error
    return NextResponse.json(
      {
        error: error.message || 'An unexpected error occurred',
        details: error,
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get job_id from query params
    const jobId = request.nextUrl.searchParams.get('job_id');

    if (!jobId) {
      return NextResponse.json(
        { error: 'Missing required parameter: job_id' },
        { status: 400 }
      );
    }

    // Get job status
    const result = await getJobStatus(jobId);

    // Return job status
    return NextResponse.json(result, { status: 200 });
  } catch (error: any) {
    console.error('API route error:', error);

    // Handle different error types
    if (error.status) {
      return NextResponse.json(
        {
          error: error.message || 'Failed to get job status',
          details: error.details,
        },
        { status: error.status }
      );
    }

    // Generic error
    return NextResponse.json(
      {
        error: error.message || 'An unexpected error occurred',
        details: error,
      },
      { status: 500 }
    );
  }
}
