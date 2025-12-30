# Deployment Fix: Worker Timeout on Payment Verification

## Issue
The Railway deployment was failing with a `CRITICAL WORKER TIMEOUT` error during payment verification. 
Error Trace: `smtplib.SMTP(self.mail.server, self.mail.port)` -> `socket.create_connection` hanging.

## Root Cause
The email sending was **synchronous** (blocking). The connection to the Gmail SMTP server was taking longer than the Gunicorn worker timeout (likely 30s), causing the application worker to be killed by the master process before it could respond to the payment verification request.

## Fix Implemented
Converted email sending to be **asynchronous** using background threads.

### Changes in `app.py`:
1. **Imported `threading`**: Added support for background execution.
2. **Updated `send_booking_confirmation_email`**:
   - Instead of sending immediately (blocking), it now starts a detached thread to handle the SMTP connection and sending.
   - The main request returns immediately, preventing the worker timeout.
3. **Updated `send_order_confirmation_email`**:
   - Applied the same async pattern to product order emails.

## Benefits
- **Zero Latency**: The user/payment gateway gets an instant success response.
- **Resilience**: Even if the email server is slow or momentarily unreachable, it won't crash the web server process.
- **Scalability**: Prevents a backlog of requests waiting for email delivery.

## Verification
Deploy the changes. The `CRITICAL WORKER TIMEOUT` error should disappear, and emails will still be delivered in the background.
