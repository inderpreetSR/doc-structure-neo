# Data Module ITM-ORG-008 — Active recall and self-assessment

**Issue:** 001  
**Information code:** Training / knowledge verification  
**Method:** Answer each question without consulting the modules. Then review the answers.

## Questions

**Q1.** An authorised direct API call works, but a web portal cannot read the response due to CORS. Who should investigate and who can own the fix?

**Q2.** An API gateway returns a 502 after a Python FastAPI service rollout. Which teams should investigate first?

**Q3.** Backend and API Platform disagree about who owns routing and customer balance calculation. How would you divide responsibility?

**Q4.** An MLOps deployment succeeds, but prediction quality declines after new input data arrives. Which functions should be involved?

**Q5.** What is the difference between Team Lead, Technical Lead, Engineering Manager and CISO decision authority?

**Q6.** What is the first question when a returned LOS case appears missing from LMS?

**Q7.** Why does the number 36 not mean 36 separate teams or employees?

**Q8.** What does A mean in RACI? Can a security approver differ from the accountable technical service owner?

## Answer key — review after retrieval

1. Frontend identifies the request/response evidence. The gateway/API Platform or Backend team that *owns the CORS headers* applies the correction; AppSec reviews policy exceptions.
2. API Platform, Backend and SRE; inspect upstream health, routes, connectivity, timeouts, recent deployment and logs.
3. API Platform usually controls shared gateway, traffic and routing policies; Backend owns service business logic and loan-level authorisation. Identify the real implementation owner.
4. Data Science, MLOps, Data Engineering, ML Engineering and potentially model validation/risk; distinguish data drift, feature defect, serving defect and true performance drift.
5. Team Lead co-ordinates daily execution; Technical Lead owns technical approach; Engineering Manager manages people/delivery; CISO oversees enterprise security strategy/policy.
6. First establish *whether business rules require this case/state to reach LMS*. Only then isolate the application/integration/reporting failure.
7. Roles are capabilities; a single person can perform multiple roles and one team can contain multiple functions.
8. A = Accountable for the scoped result. Yes: implementation ownership, change approval and security exception authority can differ.

## Suggested learning cycle

Read one data module → explain it from memory → answer one question → compare against the key → revise the identified gap.
