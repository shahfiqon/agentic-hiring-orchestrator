"""Orchestrator prompt templates for rubric generation and validation.

This module contains prompts used by the orchestrator node to:
- Generate job-specific evaluation rubrics
- Validate rubric quality and consistency
"""

RUBRIC_GENERATION_PROMPT = """You are an expert hiring orchestrator designing evaluation rubrics for technical roles.

Your task is to generate a comprehensive, job-specific evaluation rubric that will be used by a panel of agents (HR, Technical, Compliance) to assess candidate resumes.

## Requirements

Generate a rubric with exactly {rubric_categories_count} categories that cover the key competencies for this role:

1. **Rubric Structure**: The rubric must include:
   - `role_title`: The job title being evaluated (extract from the job description or derive from the role context)

2. **Category Structure**: Each category must include:
   - `name`: Clear, descriptive category name (e.g., "Agent Orchestration Depth")
   - `description`: Detailed explanation of what this category evaluates
   - `weight`: Float between 0.0 and 1.0 representing importance (all weights must sum to 1.0)
   - `is_must_have`: Boolean flag indicating if this is a critical requirement
   - `scoring_criteria`: List of at least 3 scoring levels with:
     - `score_value`: Numeric score (use 0, 3, 5 scale)
     - `description`: What this score level represents
     - `indicators`: List of 2-4 specific signals to look for

3. **Weight Distribution**:
   - All category weights must sum to exactly 1.0
   - Distribute weights based on importance (critical skills get higher weights)
   - Typical distribution: must-have categories (0.20-0.30), important (0.15-0.20), nice-to-have (0.10-0.15)

4. **Must-Have Requirements**:
   - Mark at least 1-2 categories as `is_must_have: true`
   - Must-have categories should represent core competencies without which the candidate cannot succeed

5. **Scoring Criteria**:
   - Use 0/3/5 scale: 0 (Not Present/Poor), 3 (Adequate/Good), 5 (Strong/Excellent)
   - Include specific, observable indicators for each level
   - Focus on resume evidence, not interview performance

## Few-Shot Examples

### Example 1: Senior AI Engineer - Agentic Systems

**Role Context**: Building production agentic systems with multi-agent orchestration, LLM integration, and reliability guarantees.

**Generated Rubric**:

```json
{{
  "role_title": "Senior AI Engineer - Agentic Systems",
  "categories": [
    {{
      "name": "Agent Orchestration Depth",
      "description": "Experience designing and implementing multi-agent systems with complex coordination patterns, state management, and orchestration logic",
      "weight": 0.25,
      "is_must_have": true,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No evidence of multi-agent system experience; only single-agent or basic LLM API usage",
          "indicators": [
            "Resume mentions only ChatGPT API calls or basic prompt engineering",
            "No mention of agent coordination, workflows, or orchestration",
            "Experience limited to chatbot UIs or simple Q&A systems"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some multi-agent experience but limited complexity or scale; may be experimental or academic",
          "indicators": [
            "Built proof-of-concept multi-agent systems (e.g., AutoGPT-style projects)",
            "Experience with agent frameworks (LangChain, CrewAI) but unclear production usage",
            "Mentions 'agentic workflows' but lacks detail on orchestration complexity"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Deep production experience with complex multi-agent orchestration, state management, and coordination patterns",
          "indicators": [
            "Designed production systems with 3+ specialized agents working in coordination",
            "Implemented advanced patterns: hierarchical agents, planning/execution splits, reflection loops",
            "Clear evidence of handling agent state, memory, context management at scale",
            "Experience with production observability for multi-agent systems"
          ]
        }}
      ]
    }},
    {{
      "name": "LLM Integration Expertise",
      "description": "Practical experience integrating LLMs into production systems with reliability, cost management, and structured outputs",
      "weight": 0.20,
      "is_must_have": true,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No production LLM integration experience; only API exploration or tutorials",
          "indicators": [
            "Experience limited to LLM playgrounds or notebook experiments",
            "No mention of production deployment, error handling, or reliability",
            "Resume shows only basic API usage without production context"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some production LLM integration but limited scope or maturity",
          "indicators": [
            "Integrated LLMs into production systems with basic error handling",
            "Experience with prompt engineering and basic output parsing",
            "Mentions cost awareness but unclear optimization strategies"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Extensive production LLM integration with advanced reliability and optimization techniques",
          "indicators": [
            "Implemented structured outputs, function calling, or tool use in production",
            "Built retry logic, fallback strategies, and guardrails for LLM failures",
            "Optimized LLM costs through caching, prompt compression, or model selection",
            "Experience with LLM observability: logging, tracing, latency monitoring"
          ]
        }}
      ]
    }},
    {{
      "name": "Python & FastAPI Proficiency",
      "description": "Strong Python engineering skills with FastAPI backend development experience",
      "weight": 0.20,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "Limited Python experience; primarily uses other languages",
          "indicators": [
            "Python listed but not featured in recent projects",
            "No backend framework experience mentioned",
            "Experience appears limited to scripts or data analysis"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Solid Python experience with some backend development",
          "indicators": [
            "Built backend services in Python (Flask, Django, or FastAPI)",
            "Experience with async Python or API design",
            "Comfortable with Python typing, Pydantic, or similar tools"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Expert Python backend engineer with FastAPI production experience",
          "indicators": [
            "Extensive FastAPI experience in production systems",
            "Advanced Python patterns: async/await, type hints, dependency injection",
            "Experience with Pydantic models, validation, and settings management",
            "Built scalable Python services with proper error handling and testing"
          ]
        }}
      ]
    }},
    {{
      "name": "System Design & Architecture",
      "description": "Ability to design scalable, maintainable systems with thoughtful architectural decisions",
      "weight": 0.20,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No evidence of system design experience; primarily implements features from specs",
          "indicators": [
            "Resume focuses on coding tasks without architectural context",
            "No mention of design decisions, tradeoffs, or system planning",
            "Experience limited to small scripts or single-component projects"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some system design experience with mid-sized projects",
          "indicators": [
            "Designed APIs or backend services with multiple components",
            "Experience with databases, caching, or message queues",
            "Shows awareness of scalability or maintainability concerns"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Strong system design skills with experience architecting complex systems",
          "indicators": [
            "Designed distributed systems or microservices architectures",
            "Made architectural decisions on state management, data flow, or service boundaries",
            "Experience with system scalability, fault tolerance, or performance optimization",
            "Clear evidence of designing for maintainability and extensibility"
          ]
        }}
      ]
    }},
    {{
      "name": "Domain Knowledge: Hiring/Recruiting Tech",
      "description": "Understanding of hiring workflows, ATS systems, or recruiting domain challenges",
      "weight": 0.15,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No hiring or recruiting domain experience",
          "indicators": [
            "Resume shows no work in HR tech, recruiting, or talent management",
            "No mention of ATS, resume parsing, or candidate evaluation systems",
            "Domain experience is entirely outside hiring/recruiting"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some exposure to hiring workflows or recruiting technology",
          "indicators": [
            "Built internal tools for hiring or candidate management",
            "Experience with ATS integrations or resume parsing",
            "Worked on HR-adjacent projects (e.g., employee management, onboarding)"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Deep domain expertise in hiring tech or recruiting systems",
          "indicators": [
            "Built or maintained ATS systems, recruiting platforms, or candidate evaluation tools",
            "Experience with resume parsing, candidate matching, or interview scheduling",
            "Clear understanding of hiring workflows and recruiter pain points",
            "Work in talent acquisition, HR tech, or recruiting SaaS"
          ]
        }}
      ]
    }}
  ]
}}
```

### Example 2: Backend Engineer - Distributed Systems

**Role Context**: Building scalable, fault-tolerant distributed systems with strong data consistency and performance requirements.

**Generated Rubric**:

```json
{{
  "role_title": "Backend Engineer - Distributed Systems",
  "categories": [
    {{
      "name": "Distributed Systems Experience",
      "description": "Hands-on experience building and operating distributed systems with consensus, replication, and fault tolerance",
      "weight": 0.30,
      "is_must_have": true,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No distributed systems experience; primarily monolithic applications",
          "indicators": [
            "Experience limited to single-server applications",
            "No mention of distributed databases, message queues, or service mesh",
            "Resume shows only basic web applications or scripts"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some distributed systems experience with common patterns",
          "indicators": [
            "Used distributed databases (Cassandra, MongoDB, etc.) or message queues (Kafka, RabbitMQ)",
            "Experience with microservices but unclear complexity",
            "Mentions distributed tracing or service discovery"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Deep distributed systems expertise with production experience",
          "indicators": [
            "Built systems with strong consistency guarantees (e.g., Raft, Paxos)",
            "Designed for fault tolerance: circuit breakers, retries, bulkheads",
            "Experience with distributed tracing, observability, and debugging",
            "Clear evidence of handling network partitions, eventual consistency, or consensus"
          ]
        }}
      ]
    }},
    {{
      "name": "Backend Engineering & API Design",
      "description": "Strong backend development skills with RESTful or gRPC API design",
      "weight": 0.25,
      "is_must_have": true,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "Limited backend experience; primarily frontend or full-stack with frontend focus",
          "indicators": [
            "Resume emphasizes frontend technologies",
            "Minimal API design or backend architecture experience",
            "Backend work appears superficial or tutorial-level"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Solid backend engineering with API design experience",
          "indicators": [
            "Built RESTful APIs with proper error handling and validation",
            "Experience with backend frameworks (Spring, Express, FastAPI, etc.)",
            "Designed APIs for internal or external consumption"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Expert backend engineer with advanced API design patterns",
          "indicators": [
            "Designed high-throughput APIs with rate limiting, caching, and optimization",
            "Experience with gRPC, GraphQL, or advanced API patterns",
            "Built versioned, backward-compatible APIs at scale",
            "Strong understanding of API security, authentication, and authorization"
          ]
        }}
      ]
    }},
    {{
      "name": "Performance & Scalability",
      "description": "Experience optimizing systems for high throughput, low latency, and horizontal scalability",
      "weight": 0.20,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No evidence of performance optimization or scalability work",
          "indicators": [
            "Resume does not mention performance, latency, or scalability",
            "Projects appear small-scale without performance constraints",
            "No profiling, optimization, or load testing mentioned"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some performance optimization experience",
          "indicators": [
            "Optimized database queries or API response times",
            "Experience with caching (Redis, Memcached) or CDNs",
            "Mentions load testing or performance monitoring"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Deep performance engineering expertise",
          "indicators": [
            "Optimized systems for millions of requests per second or sub-millisecond latency",
            "Designed horizontal scaling strategies (sharding, partitioning, load balancing)",
            "Profiled and optimized hot paths, memory usage, or CPU bottlenecks",
            "Experience with performance testing tools and production profiling"
          ]
        }}
      ]
    }},
    {{
      "name": "Data Engineering & Storage",
      "description": "Experience with databases, data modeling, and storage systems",
      "weight": 0.15,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "Minimal database experience beyond basic CRUD operations",
          "indicators": [
            "Only mentions basic SQL or ORM usage",
            "No data modeling or schema design experience",
            "Resume does not emphasize data systems"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Solid database experience with schema design",
          "indicators": [
            "Designed database schemas for production applications",
            "Experience with both SQL and NoSQL databases",
            "Built data pipelines or ETL workflows"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Expert in data systems with complex data modeling",
          "indicators": [
            "Designed data models for high-scale systems (billions of records)",
            "Experience with advanced database features: sharding, replication, indexing strategies",
            "Built real-time data pipelines or stream processing systems",
            "Deep knowledge of database internals or storage engine trade-offs"
          ]
        }}
      ]
    }},
    {{
      "name": "Operational Excellence",
      "description": "Experience with production operations, monitoring, and incident response",
      "weight": 0.10,
      "is_must_have": false,
      "scoring_criteria": [
        {{
          "score_value": 0,
          "description": "No production operations experience; development-only focus",
          "indicators": [
            "Resume does not mention deployments, monitoring, or on-call",
            "No CI/CD, observability, or incident response experience",
            "Projects appear to be non-production or educational"
          ]
        }},
        {{
          "score_value": 3,
          "description": "Some production operations experience",
          "indicators": [
            "Deployed services to production with CI/CD pipelines",
            "Set up monitoring and alerting for production systems",
            "Participated in on-call rotations or incident response"
          ]
        }},
        {{
          "score_value": 5,
          "description": "Strong operational discipline with SRE mindset",
          "indicators": [
            "Built comprehensive observability: metrics, logs, traces, dashboards",
            "Led incident response and post-mortem processes",
            "Designed for reliability: SLOs, error budgets, graceful degradation",
            "Experience with chaos engineering or disaster recovery"
          ]
        }}
      ]
    }}
  ]
}}
```

## Input Context

**Job Description**:
{job_description}

**Company Context**:
{company_context}

## Instructions

1. Extract or derive the role_title from the job description (e.g., "Senior AI Engineer - Agentic Systems", "Backend Engineer - Distributed Systems")
2. Analyze the job description to identify the {rubric_categories_count} most important competencies for this role
3. Consider the company context to tailor category weights and must-have flags
4. Create specific, observable scoring criteria with concrete indicators
5. Ensure weights sum to exactly 1.0 and reflect true importance hierarchy
6. Mark 1-2 categories as must-have based on critical success factors
7. Generate output as a valid Rubric object matching the schema exactly

## Output

Generate a Rubric object with {rubric_categories_count} categories following the structure demonstrated in the examples above.
"""

RUBRIC_VALIDATION_PROMPT = """You are a rubric quality validator ensuring evaluation rubrics are well-formed and effective.

Review the following rubric and check for:

1. **Mathematical Validity**:
   - Do all category weights sum to exactly 1.0?
   - Are all weights between 0.0 and 1.0?

2. **Structural Completeness**:
   - Does each category have a clear name, description, and scoring criteria?
   - Are there at least 3 scoring levels (0, 3, 5) for each category?
   - Do scoring criteria include specific indicators?

3. **Content Quality**:
   - Are the categories relevant to the job description?
   - Are the indicators specific and observable from resumes?
   - Do the scoring levels show clear differentiation?
   - Is at least one category marked as must-have?

4. **Consistency**:
   - Do category weights reflect their is_must_have status?
   - Are must-have categories weighted appropriately (typically 0.20-0.30)?
   - Do the scoring criteria align with the category descriptions?

## Rubric to Validate

{rubric_json}

## Output

Return a validation report indicating:
- Whether the rubric passes validation (true/false)
- List of any issues found
- Suggested improvements if applicable
"""
