# TODO - Fix Apply Redirect to Company Website

- [x] Update backend schema: add `website_url` to `CompanyProfile` in `backend/app/models.py`
- [x] Update backend company profile API: accept/save `website_url` in `backend/app/routes/company.py` (`/company/profile`)
- [x] Update backend jobs API: return `apply_url` from `job.company.website_url` in `backend/app/routes/job.py` (`GET /jobs`)
- [x] Update frontend company dashboard UI: add input for Company Website URL and include it in save payload in `frontend/src/pages/CompanyDashboard.jsx`
- [x] Update frontend apply button behavior: redirect user to the company website URL (opened in new tab) when applying to a job
- [x] Test: verify backend /jobs API and application endpoints return the company's URL, and the frontend opens it upon application submission


