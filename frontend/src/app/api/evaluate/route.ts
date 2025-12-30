import { NextRequest, NextResponse } from 'next/server';
import { submitEvaluation } from '@/lib/api';
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

    // Call backend API
    const result = await submitEvaluation(body);

    // Return results
    return NextResponse.json(result, { status: 200 });
  } catch (error: any) {
    console.error('API route error:', error);

    // Handle different error types
    if (error.status) {
      return NextResponse.json(
        {
          error: error.message || 'Evaluation failed',
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
