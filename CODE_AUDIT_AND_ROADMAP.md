# PujaPath - Comprehensive Code Audit & Roadmap

**Date:** 2026-02-05
**Status:** Audit Completed
**Scope:** Full Project Analysis (`d:\first-project\first-project`)

## 1. Research & Documentation Status

**User Note:** "We have done a research before also that folder do exists check that as well."

**Agent Verification:**
*   **Search Results:** I performed a thorough search of `d:\first-project` and `d:\first-project\first-project` for folders named "research", "audit", "docs", "planning", or "roadmap".
*   **Finding:** No specific folder named "research" was found in the current file structure.
*   **Existing Documentation:** However, the project root contains extensive documentation which likely serves as the research corpus:
    *   `FEATURES.md` (Comprehensive feature roadmap)
    *   `SETUP_GUIDE.md`
    *   `DEPLOYMENT_FIX.md`
    *   `PANDIT_PAYMENT_INTEGRATION.md`
    *   `ASYNC_EMAIL_FIX_SUMMARY.md`

If there is a specific separate folder you expect to see, it may be on a different branch or was not synced to this environment.

---

## 2. CRITICAL BUGS (Immediate Action Required)

The following bugs are breaking core functionality and must be fixed immediately.

### BUG 1: Dead Code in Order Confirmation (Payment Bypass)
*   **Location:** `app.py:1342-1347`
*   **Issue:** The `order_confirmation` route returns the template *before* checking the payment status. The payment check code follows the return statement and is therefore unreachable/dead code.
*   **Impact:** Users can view the confirmation page without paying if they guess functionality.

### BUG 2: Race Condition in Booking/Order Numbers
*   **Location:** `app.py:1122`, `1290`, `1419`
*   **Issue:** Uses `Order.query.count() + 1` to generate sequential IDs.
*   **Impact:** if two users book simultaneously, they will get the same Order ID, causing a database crash (Unique Constraint Violation).

### BUG 3: Booking Cancellation Type Mismatch
*   **Location:** `app.py:2251`
*   **Issue:** `if booking.user_id != user_id:` compares an Integer (from DB) with a String (from `get_jwt_identity()`).
*   **Impact:** This comparison always evaluates to `True` (inequality), meaning users are *always* blocked from cancelling their own bookings.

### BUG 4: User ID Type Mismatch (Dashboard Broken)
*   **Location:** All User Dashboard routes (`app.py:2167`, `2174`, `2272`, etc.)
*   **Issue:** `get_jwt_identity()` returns a string, but DB queries expect an integer.
*   **Impact:** User dashboard, orders, and booking lists will likely come up empty or error out.

### BUG 5: Bare Except Clauses
*   **Location:** `app.py:1209`, `1249`; `models/order.py:53`
*   **Issue:** `except:` blocks catch *everything*, including system interrupts and typos.
*   **Impact:** Makes debugging extremely difficult as it swallows legitimate errors without trace.

### BUG 6: Missing Database Column (`payment_reference`)
*   **Location:** `app.py:1560`
*   **Issue:** Code tries to assign `order.payment_reference = ...`, but the `Order` model does not have this column defined.
*   **Impact:** Runtime crash upon successful payment verification.

---

## 3. SECURITY VULNERABILITIES (Critical)

### SEC 1: Exposed Production Credentials
*   **Location:** `.env` file
*   **Issue:** Production database credentials, Razorpay keys, and AWS secrets are in the `.env` file which is present in the codebase.
*   **Remediation:** Rotate these keys immediately. Ensure `.env` is git-ignored.

### SEC 2: Admin Init Route Publicly Accessible
*   **Location:** `app.py:2123` (`/admin/init`)
*   **Issue:** Public GET endpoint that exposes/sets the admin password to a hardcoded string (`admin123`).

### SEC 3: Destructive Routes Publicly Accessible
*   **Location:** `/api/clear-data` and `/api/seed-data`
*   **Issue:** Unauthenticated users can wipe the entire production database by visiting a URL.

### SEC 4: JWT Token Leak via URL
*   **Location:** `app.py:834`
*   **Issue:** Passing JWT tokens and user data as URL query parameters (`/?token=...`).
*   **Impact:** Tokens are logged in browser history, proxy logs, and server access logs.

### SEC 5: XSS Vulnerability in Cart
*   **Location:** `base.html:377`
*   **Issue:** Uses `.innerHTML` to render product names from LocalStorage.
*   **Impact:** Malicious script injection possible via local storage manipulation.

### SEC 6: No CSRF Protection
*   **Issue:** The app lacks CSRF tokens on form submissions (Checkout, Contact, Login).

### SEC 7: Detailed Debug Prints (Verified)
*   **Location:** `app.py:95-96`
*   **Issue:** The application prints sensitive email configuration (Server, Username) to the console on startup.
*   **Remediation:** Remove these print statements immediately.

### SEC 8: Unprotected User Dashboard Routes (Verified)
*   **Location:** `app.py:2346-2369` (`/user/dashboard`, `/user/orders`, etc.)
*   **Issue:** These HTML serving routes have no `@jwt_required` decorators.
*   **Impact:** Any unauthenticated user can access the dashboard pages (though data loading might fail, the UI structure is exposed).

---

## 4. CODE QUALITY & QUALITY OF LIFE

1.  **Monolithic Architecture:** `app.py` is ~2,400 lines long. Needs splitting into blueprints.
2.  **Contact Form is Dummy:** `app.py:919` just logs the message but does not save it to DB or send an email. Users think they contacted support but didn't.
3.  **Duplicate Email Logic:** Code contains multiple almost identical `send_async` functions nested inside other functions.
4.  **Deprecated Time Functions:** Uses `datetime.utcnow()` which is deprecated.
5.  **Floating Point Currency:** Uses `Float` for money. Should use `Numeric` or Integer.
6.  **Hardcoded Values:** Pandit booking price is hardcoded to `999`.

---

## 5. SUGGESTED ROADMAP (Phase 2 & 3)

### Immediate Priorities (Next Sprint)
1.  **Fix High-Severity Bugs** (Dead code, Race conditions, Type mismatches).
2.  **Security Hardening** (Secure routes, separate secrets, fix XSS).
3.  **Missing "Forgot Password" Flow**: Critical for user retention.

### Feature Additions
*   **Search & Filters**: Allow users to filter pandits by language/location.
*   **Review System**: Post-puja ratings and testimonials.
*   **Invoices**: PDF generation for bookings/orders.
*   **Calendar Integration**: Real availability checking for Pandits instead of boolean availability.
*   **Notifications**: WhatsApp/SMS integration for updates.
*   **Inventory Management**: Track stock levels for products.

---

**Next Steps:**
Please review this document. Upon your approval, I can begin addressing the **Critical Bugs** followed by the **Security Vulnerabilities**.
 