# FinSentry Frontend-Backend Integration

## 🎉 Integration Complete!

### What Was Built

Successfully integrated the React frontend with the FastAPI backend to create a full-stack application.

## 📋 Components Created

### 1. API Configuration (`/src/config/api.ts`)
- Centralized API endpoint definitions
- Base URLs for HTTP and WebSocket
- Storage keys for tokens
- All endpoints organized by feature:
  - Authentication (register, login, refresh, me, logout)
  - Invoice management (upload, list, detail, approve, reject, delete)
  - Batch management (create, list, detail, update, delete, status)
  - Dashboard analytics (metrics, vendors, throughput, latency, model metrics, CSV export)
  - Chat interface (message, history)
  - WebSocket endpoints (invoice, batch, dashboard metrics, chat)

### 2. API Client (`/src/utils/apiClient.ts`)
- Token management (get, set, clear)
- Automatic token refresh on 401 errors
- Error handling with APIError class
- Convenience methods:
  - `api.get()` - GET requests
  - `api.post()` - POST with JSON body
  - `api.put()` - PUT with JSON body
  - `api.delete()` - DELETE requests
  - `api.upload()` - File uploads with multipart/form-data
  - `createWebSocket()` - WebSocket connection with authentication

### 3. Authentication System

#### AuthContext (`/src/contexts/AuthContext.tsx`)
- AuthProvider component for app-wide authentication state
- `useAuth()` hook with:
  - `user` - Current user object
  - `isAuthenticated` - Authentication status
  - `isLoading` - Loading state
  - `login(email, password)` - OAuth2 password flow login
  - `register(email, username, password, fullName)` - User registration
  - `logout()` - Clear tokens and reset state
  - `updateUser(userData)` - Update user information

#### Login Page (`/src/pages/LoginPage.tsx`)
- Beautiful gradient background design
- Email/password form with validation
- Quick demo login buttons (Admin, Manager, User)
- Error handling and loading states
- Auto-redirect after successful login

#### Logout Button (`/src/components/LogoutButton.tsx`)
- Shows current username
- Confirmation dialog
- Logout icon button

### 4. Updated Hooks

#### Dashboard Metrics Hook (`/src/hooks/useDashboardMetrics.ts`)
- ✅ Uses real API client instead of mock fetch
- ✅ Connects to backend dashboard endpoints
- ✅ WebSocket integration for real-time updates
- ✅ CSV export functionality
- ✅ Filter support (date range, vendors, statuses, batches)

### 5. Application Integration

#### Main Entry Point (`/src/main.tsx`)
- Wraps app with AuthProvider
- Shows LoginPage when not authenticated
- Shows main App when authenticated
- Loading state during auth check

#### App Component (`/src/App.tsx`)
- Added LogoutButton to header
- Shows current user
- Maintains all existing functionality

## 🚀 Running the Application

### Backend
```bash
cd /Users/admin/gst-extractor/backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
**Status:** ✅ Running on http://localhost:8000

### Frontend
```bash
cd /Users/admin/gst-extractor/finsentry-ui
npm run dev
```
**Status:** ✅ Running on http://localhost:3000

## 🔐 Demo Credentials

| Role    | Email                    | Password    |
|---------|--------------------------|-------------|
| Admin   | admin@finsentry.com      | Admin@123   |
| Manager | manager@finsentry.com    | Manager@123 |
| User    | user@finsentry.com       | User@123    |

## 📊 Integration Status

### ✅ Completed
- [x] API configuration structure
- [x] HTTP client with authentication
- [x] Token management and refresh
- [x] Authentication context and hooks
- [x] Login page with demo credentials
- [x] Logout functionality
- [x] Dashboard metrics using real API
- [x] WebSocket helper functions
- [x] Error handling
- [x] CORS configuration
- [x] Both servers running

### 🔄 In Progress
- [x] ✅ Fixed WebSocket endpoint (was `/ws/invoiceStatus`, now `/ws/dashboard/metrics`)
- [x] ✅ Fixed upload endpoint (now uses batch creation + file upload flow)
- [x] ✅ Upload service uses authenticated API client
- [ ] Testing complete upload flow
- [ ] Verifying real-time updates

### ⏳ To Do
- [ ] Update invoice stream hook (create per-invoice WebSockets)
- [ ] Update batch status hook (connect to batch WebSocket)
- [ ] Connect chat to backend streaming
- [ ] Test file upload end-to-end
- [ ] Test all WebSocket connections
- [ ] End-to-end integration testing

## 🐛 Issues Fixed

### Issue #1: WebSocket Connection Failed
**Error:** `WebSocket connection to 'ws://localhost:8000/ws/invoiceStatus' failed`

**Root Cause:** Frontend was trying to connect to non-existent endpoint.

**Solution:** 
- Updated `websocket.ts` to connect to `/ws/dashboard/metrics` (global metrics)
- Individual invoice/batch WebSockets should be created per-item as needed

**Files Changed:**
- `finsentry-ui/src/services/websocket.ts`

### Issue #2: Upload Endpoint 404
**Error:** `Failed to load resource: 404 (Not Found) (uploadInvoices)`

**Root Cause:** Frontend was POSTing to `/api/uploadInvoices` which doesn't exist.

**Backend Upload Flow:**
1. Create batch: `POST /api/batches` → Returns `{ id, batch_number }`
2. Upload files: `POST /api/invoices/upload` with `batch_id` form field

**Solution:**
- Updated `upload.ts` to create batch first, then upload files
- Now uses `api.post()` and `api.upload()` with authentication
- Proper FormData structure with `batch_id` field

**Files Changed:**
- `finsentry-ui/src/services/upload.ts`

**See:** [INTEGRATION_FIXES.md](./INTEGRATION_FIXES.md) for detailed fix documentation.

## 🔗 API Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - Login (OAuth2 password flow)
- POST `/api/auth/refresh` - Refresh access token
- GET `/api/auth/me` - Get current user
- POST `/api/auth/logout` - Logout

### Invoices
- POST `/api/invoices/upload` - Upload invoice file
- GET `/api/invoices` - List invoices
- GET `/api/invoices/{id}` - Get invoice details
- POST `/api/invoices/{id}/approve` - Approve invoice
- POST `/api/invoices/{id}/reject` - Reject invoice
- DELETE `/api/invoices/{id}` - Delete invoice

### Batches
- POST `/api/batches` - Create batch
- GET `/api/batches` - List batches
- GET `/api/batches/{id}` - Get batch details
- PUT `/api/batches/{id}` - Update batch
- DELETE `/api/batches/{id}` - Delete batch
- GET `/api/batches/{id}/status` - Get batch status

### Dashboard
- GET `/api/dashboard/metrics` - Get dashboard metrics
- GET `/api/dashboard/vendors` - Get vendor analytics
- GET `/api/dashboard/throughput` - Get throughput data
- GET `/api/dashboard/latency` - Get latency data
- GET `/api/dashboard/model/metrics` - Get ML model metrics
- GET `/api/dashboard/export/csv` - Export dashboard data as CSV

### Chat
- POST `/api/chat/message` - Send chat message
- GET `/api/chat/history/{batchId}` - Get chat history

### WebSocket
- WS `/ws/invoices/{id}` - Real-time invoice updates
- WS `/ws/batches/{id}` - Real-time batch updates
- WS `/ws/dashboard/metrics` - Real-time dashboard metrics
- WS `/ws/chat` - Real-time chat

## 🎨 User Flow

1. **User opens http://localhost:3000**
   - Sees beautiful login page

2. **User clicks "Admin" demo button**
   - Form auto-fills with admin@finsentry.com / Admin@123

3. **User clicks "Sign In"**
   - Frontend sends POST to `/api/auth/login` (OAuth2 form data)
   - Backend validates credentials
   - Returns `access_token` and `refresh_token`
   - Frontend stores tokens in localStorage
   - Frontend calls `/api/auth/me` to get user data
   - User is redirected to main app

4. **Dashboard loads with real data**
   - Frontend calls `/api/dashboard/metrics`
   - Backend queries SQLite database
   - Returns real metrics (processed invoices, flagged rate, latency, etc.)
   - Dashboard displays live data

5. **WebSocket connects**
   - Frontend establishes WebSocket connections
   - Real-time updates flow from backend
   - Dashboard updates automatically

6. **User uploads invoice**
   - Frontend uses `api.upload()` with multipart/form-data
   - Backend processes invoice with AI agents
   - Real-time status updates via WebSocket

7. **User logs out**
   - Clicks logout button in header
   - Frontend clears tokens
   - User returns to login page

## 🛠️ Technical Details

### Token Management
- Access tokens stored in `localStorage` as `finsentry_access_token`
- Refresh tokens stored as `finsentry_refresh_token`
- Automatic refresh on 401 responses
- Bearer token in Authorization header

### Error Handling
- Custom `APIError` class with status, statusText, and data
- User-friendly error messages
- Console logging for debugging
- Toast notifications for user feedback

### WebSocket Integration
- Token passed in query string or header
- Automatic reconnection on disconnect
- Error handling and logging
- Message parsing and validation

### CORS Configuration
- Backend allows `http://localhost:3000` and `http://localhost:5173`
- Credentials included in requests
- Pre-flight requests handled

## 📝 Next Steps

1. **Test the integration:**
   - Open http://localhost:3000
   - Try demo login buttons
   - Verify dashboard loads real data
   - Test upload functionality

2. **Update remaining hooks:**
   - Invoice stream hook
   - Batch status hook
   - Chat integration

3. **End-to-end testing:**
   - Complete user workflows
   - Error scenarios
   - Edge cases

## 🎯 Success Criteria

- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ Login page renders
- ✅ Authentication context available
- ✅ API client configured
- ⏳ Login flow works (testing in progress)
- ⏳ Dashboard loads real data (testing in progress)
- ⏳ WebSocket connects (testing in progress)

## 🔍 Troubleshooting

### If login fails:
1. Check backend is running: http://localhost:8000/docs
2. Check console for errors
3. Verify credentials match database
4. Check network tab for API calls

### If dashboard shows no data:
1. Verify token is stored in localStorage
2. Check Authorization header in requests
3. Verify backend endpoints return data
4. Check console for API errors

### If WebSocket doesn't connect:
1. Verify backend WebSocket endpoint is running
2. Check token is included in connection
3. Look for connection errors in console
4. Verify CORS configuration

## 📚 Documentation

- Frontend API docs: See `src/config/api.ts`
- Backend API docs: http://localhost:8000/docs
- Authentication flow: See `src/contexts/AuthContext.tsx`
- API client usage: See `src/utils/apiClient.ts`

---

**Integration Date:** November 8, 2024  
**Status:** ✅ Core integration complete, testing in progress  
**Next Milestone:** Complete end-to-end workflow testing
