# Project Rules & Guidelines

## 1. Cost Efficiency
- Prioritize AWS Free Tier and serverless/pay-per-use services.
- Avoid persistent compute resources unless absolutely necessary.
- Monitor AWS usage and set up billing alerts.

## 2. Data Privacy & Ethics
- Do not collect or store personally identifiable information (PII) unless explicitly permitted.
- Anonymize user data where possible.
- Comply with YouTube API terms of service.

## 3. Modularity & Reproducibility
- Organize code into clear modules (data ingestion, processing, analysis, visualization).
- Use configuration files for parameters and secrets (never hardcode API keys).
- Document all steps and decisions.

## 4. Scalability
- Design pipeline to handle increasing data volumes with minimal code changes.
- Use S3 for all intermediate and final data storage.

## 5. Business Relevance
- Focus on extracting actionable insights for lead generation, sales, and marketing.
- Prioritize features that demonstrate direct business value (e.g., lead scoring, intent detection).

## 6. Automation
- Automate data pulls, processing, and reporting where possible.
- Use AWS Step Functions or EventBridge for orchestration.

## 7. Testing & Quality
- Write unit and integration tests for all major components.
- Validate model outputs and lead generation logic.

---

*These rules ensure the project remains focused, ethical, and impressive to employers.*
