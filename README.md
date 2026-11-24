# UniCareer

UniCareer connects students with job opportunities and provides employer and administrator workflows.

## Integrated workflows

- Candidates can browse and filter approved jobs, maintain account details separately from multiple structured CV versions, apply once per job, and track application status.
- Employers can manage their company profile and job posts, review applications, view application CVs, and update application status.
- Administrators can approve or reject job posts and activate or deactivate accounts.
- Public job listings include only active, approved, non-expired jobs. Employer data and CV downloads are restricted by ownership and role.

## Run locally (Windows PowerShell)

1. Create a MySQL database named `unicareer_db`.
2. From the `DuAn_Nhom8-main` project root, create and activate a virtual environment, then install the backend dependencies:

   ```powershell
   python -m venv backend\.venv
   .\backend\.venv\Scripts\Activate.ps1
   python -m pip install -r backend\requirements.txt
   Copy-Item backend\.env.example backend\.env
   ```

3. Edit `backend\.env` and set `DATABASE_URL` and a private `SECRET_KEY` of at least 32 characters. Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The API refuses to start if either required setting is missing or the secret is too short. Keep `.env` out of source control. To enable CV analysis, add a Gemini API key as `GEMINI_API_KEY`; `GEMINI_MODEL` defaults to `gemini-3.5-flash-lite`. Candidates can create a CV with the builder or upload a PDF/DOCX up to 10 MB. Either type can be analyzed after explicit consent.
4. Start the API from the project root:

   ```powershell
   Set-Location backend
   uvicorn app.main:app --reload
   ```

5. Open `http://127.0.0.1:8000/frontend/index.html`. API documentation is available at `http://127.0.0.1:8000/docs`.

The application creates missing tables and seeds the candidate, employer, and admin roles at startup. It does not create an administrator account. To provision one, first register a trusted account, then run the following SQL in the configured database, replacing the email:

```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@example.com';
DELETE FROM user_roles
WHERE user_id = (SELECT id FROM users WHERE email = 'admin@example.com');
INSERT INTO user_roles (user_id, role_id)
SELECT users.id, roles.id
FROM users
JOIN roles ON roles.name = 'admin'
WHERE users.email = 'admin@example.com';
```

Sign out and sign back in after provisioning so the account receives the administrator role in its session.

CV analysis sends the selected CV content and job description to Google Gemini only after the candidate explicitly consents. Candidates can separately opt in to let employers analyze a CV attached to an application. Analysis is advisory, is not a hiring decision, and its result is stored in the application database. Do not enable this feature without informing users about Google's data processing.

## Run backend workflow tests

From the project root:

```powershell
python -m pip install -r backend\requirements-test.txt
python -m pytest backend\tests
```

The workflow tests use SQLite and mock Gemini responses; they do not require a MySQL server or a Gemini API key.
