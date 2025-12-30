# Agentic Hiring Orchestrator - Frontend

A modern Next.js web application for the Agentic Hiring Orchestrator system. This frontend provides an intuitive interface for submitting candidate evaluations and viewing comprehensive multi-agent assessment results.

## Features

- **Simple Evaluation Workflow**: Submit job descriptions and resumes through a clean, user-friendly form
- **Comprehensive Results Display**: View detailed evaluation results including:
  - Decision summary with overall fit score and recommendation
  - Rubric breakdown with weighted categories
  - Individual agent reviews (HR, Technical, Compliance)
  - Disagreement analysis between agents
  - Structured interview plans
- **Real-time Backend Status**: Monitor backend connectivity and health
- **Export Capabilities**: Download evaluation results as JSON
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices

## Technology Stack

- **Framework**: Next.js 14+ with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS for utility-first styling
- **Forms**: React Hook Form with Zod validation
- **HTTP Client**: Axios for API communication
- **Icons**: Lucide React

## Prerequisites

- Node.js 18+ and npm
- Backend API running (default: http://localhost:8000)

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment file and configure:

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Agentic Hiring Orchestrator
```

### 3. Start Development Server

```bash
npm run dev
```

The application will be available at http://localhost:3000

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── layout.tsx           # Root layout with header/footer
│   │   ├── page.tsx             # Home page
│   │   ├── evaluate/
│   │   │   └── page.tsx         # Evaluation form page
│   │   ├── results/
│   │   │   └── page.tsx         # Results display page
│   │   ├── api/
│   │   │   └── evaluate/
│   │   │       └── route.ts     # API route proxy
│   │   └── globals.css          # Global styles
│   ├── components/              # Reusable UI components
│   │   ├── Alert.tsx
│   │   ├── Badge.tsx
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Container.tsx
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   ├── Tabs.tsx
│   │   ├── Accordion.tsx
│   │   ├── ProgressBar.tsx
│   │   ├── Spinner.tsx
│   │   └── results/             # Results-specific components
│   │       ├── DecisionSummary.tsx
│   │       ├── RubricDisplay.tsx
│   │       ├── AgentReviews.tsx
│   │       ├── DisagreementSection.tsx
│   │       └── InterviewPlanSection.tsx
│   └── lib/                     # Utilities and services
│       ├── api.ts               # Backend API client
│       ├── types.ts             # TypeScript type definitions
│       ├── utils.ts             # Utility functions
│       └── validation.ts        # Zod validation schemas
├── public/                      # Static assets
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
└── .env.local                   # Environment variables (create from .env.example)
```

## Usage Guide

### Submitting an Evaluation

1. Navigate to the home page at http://localhost:3000
2. Click "Start Evaluation" or navigate to `/evaluate`
3. Fill in the form:
   - **Job Description** (required): Paste the full job description
   - **Resume** (required): Paste the candidate's resume or upload a text file
   - **Company Context** (optional): Add additional context about the company or role
4. Click "Start Evaluation"
5. Wait for the evaluation to complete (typically 1-2 minutes)
6. The results will be displayed inline on the same page

### Viewing Results

The results display includes:

- **Decision Summary**: Overall fit score, recommendation, confidence level, strengths, risks, and gaps
- **Rubric**: The evaluation rubric generated from the job description
- **Agent Reviews**: Tabbed view of HR, Technical, and Compliance agent assessments
- **Disagreements**: Analysis of significant score disagreements between agents
- **Interview Plan**: Structured interview questions organized by interviewer role

### Exporting Results

Click the "Export Results (JSON)" button to download the complete evaluation data as a JSON file.

## API Integration

The frontend communicates with the backend through:

- **Base URL**: Configured via `NEXT_PUBLIC_API_BASE_URL`
- **Endpoints**:
  - `GET /health` - Check backend health status
  - `GET /config` - Get backend configuration
  - `POST /evaluate` - Submit evaluation request

All API calls are proxied through Next.js API routes for better error handling and security.

## Type Safety

The frontend uses TypeScript types that mirror the backend Pydantic models:

- `EvaluationRequest` / `EvaluationResponse`
- `Rubric`, `RubricCategory`, `ScoringCriteria`
- `AgentReview`, `CategoryScore`, `Evidence`
- `DecisionPacket`, `Disagreement`
- `InterviewPlan`, `InterviewQuestion`
- `WorkingMemory`, `KeyObservation`

These types ensure type safety across the entire application stack.

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

- Use TypeScript for all new code
- Follow the existing component structure
- Use Tailwind CSS utility classes for styling
- Ensure responsive design for all components
- Add proper error handling and loading states

## Troubleshooting

### Backend Connection Issues

If you see "Backend: Offline" on the home page:

1. Ensure the backend server is running
2. Check that `NEXT_PUBLIC_API_BASE_URL` in `.env.local` matches your backend URL
3. Verify CORS is properly configured on the backend

### Evaluation Timeout

If evaluations are timing out:

1. Check backend logs for errors
2. Ensure LLM provider credentials are configured
3. Increase the timeout in `src/lib/api.ts` if needed (default: 5 minutes)

### Build Errors

If you encounter build errors:

1. Delete `.next` folder and `node_modules`
2. Run `npm install` again
3. Run `npm run build`

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

When contributing to the frontend:

1. Maintain type safety with TypeScript
2. Follow the existing component patterns
3. Ensure responsive design
4. Add proper error handling
5. Update this README if adding new features

## License

Part of the Agentic Hiring Orchestrator project.
