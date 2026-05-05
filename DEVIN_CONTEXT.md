# Devin Context: Walmart Test Coverage Use Case

Company: Walmart

Use Case: Improve the automated test coverage for the legacy accounting service. 

Why this matters: Walmart has an extremely high transaction volume with clients across stores, eCommerce websites via payments and returns ; distributors and suppliers, taxes and general marketplace operations. Strong accounting test coverage helps reduce regression risk, improve auditibility and support reliable financial operations to improve supply chain optimization and automation and better performance indicator accuracy and integrity.

Repository: python-accounting

Goal: Use Devin to inspect the existing tests, identify coverage gaps and add meaningful pytest coverage without changing existing product behavior while maintaining ease of modification. 

Suggested test focus area: 
'- Ledger integrity
'- Transaction posting
'- Accounts receivables
'- Accounts payables
'- Tax handling
'- Reporting periods
'- Financial reports
'- Aging schedules

Instructions for Devin: First inspect the current test suite and project structure. Then propose 3 to 5 target tests that improve confidence in the accounting domain logic. Implement the tests, run pytest, and open a pull request with a concise summary of what was added and why.