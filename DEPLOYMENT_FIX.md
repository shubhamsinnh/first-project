# Deployment Fix - ModuleNotFoundError: No module named 'main'

## Issue
The deployment was failing with the error:
```
ModuleNotFoundError: No module named 'main'
```

This occurred because gunicorn was trying to import `main:app` but the Flask application is actually in `app.py` with the variable name `app`.

## Root Cause
Railway's default Python buildpack (nixpacks) was trying to auto-detect the entry point and defaulted to `main:app`, which doesn't exist in this project.

## Solution Applied

### 1. Created `Procfile`
Added a Procfile with the correct entry point:
```
web: gunicorn app:app
```

This tells Railway/Heroku-style platforms to use the `app` variable from the `app.py` module.

### 2. Updated `nixpacks.toml`
Added explicit start command:
```toml
[providers.python]
pythonVersion = "3.12"

[start]
cmd = "gunicorn app:app --bind 0.0.0.0:$PORT"
```

This ensures nixpacks uses the correct entry point and binds to the correct port.

## Files Modified
1. **Created**: `Procfile` - Defines web process entry point
2. **Updated**: `nixpacks.toml` - Added [start] section with correct command

## Deployment Instructions

1. **Commit the changes**:
   ```bash
   git add Procfile nixpacks.toml
   git commit -m "Fix deployment: Use app:app instead of main:app for gunicorn"
   git push
   ```

2. **Railway will automatically redeploy** with the correct configuration

3. **Verify deployment** by checking the logs - you should see:
   ```
   [INFO] Starting gunicorn
   [INFO] Listening at: http://0.0.0.0:8080
   [INFO] Booting worker with pid: X
   ```
   Without any `ModuleNotFoundError`

## Why This Happened

Railway's nixpacks buildpack has default heuristics to detect Python applications:
- It looks for common entry points like `main.py`, `main:app`, `wsgi.py`, etc.
- If it can't find them, it defaults to `main:app`
- Our application uses `app.py` as the main file, which wasn't auto-detected

## Alternative Entry Point Options

If you ever need to change the entry point, you can use any of these patterns:
- `app:app` - Current: app.py with variable app
- `app:application` - If you rename the variable to application
- `main:app` - If you rename app.py to main.py
- `wsgi:app` - If you create a wsgi.py file

## Testing Locally with Gunicorn

To test if gunicorn works correctly before deploying:
```bash
source .venv/bin/activate
gunicorn app:app --bind 127.0.0.1:8000
```

Then visit http://127.0.0.1:8000 in your browser.

## Additional Notes

- The Procfile is the standard way to define process types for Heroku-compatible platforms
- The nixpacks.toml [start] command provides a backup/override for Railway-specific deployments
- Both files now point to the same entry point for consistency
- Gunicorn 23.0.0 is already in requirements.txt, so no changes needed there
