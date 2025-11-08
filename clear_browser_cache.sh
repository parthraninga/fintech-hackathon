#!/bin/bash

# Clear Browser Cache Helper Script
# This script helps resolve browser caching issues after code changes

echo "🔄 FinSentry Frontend Cache Clear Helper"
echo "========================================"
echo ""
echo "The frontend code has been updated, but your browser may have cached the old code."
echo ""
echo "📋 Please follow these steps:"
echo ""
echo "1️⃣  Open your browser at http://localhost:3000"
echo ""
echo "2️⃣  Do a HARD REFRESH to clear cache:"
echo "   • macOS Chrome/Edge:  Cmd + Shift + R"
echo "   • macOS Safari:        Cmd + Option + R"
echo "   • macOS Firefox:       Cmd + Shift + R"
echo ""
echo "3️⃣  Or open DevTools and:"
echo "   • Right-click the refresh button"
echo "   • Select 'Empty Cache and Hard Reload'"
echo ""
echo "4️⃣  Expected behavior after refresh:"
echo "   ✅ Login page loads"
echo "   ✅ Click 'Admin' demo button"
echo "   ✅ Click 'Sign In'"
echo "   ✅ Dashboard loads with user in header"
echo "   ✅ No WebSocket errors in console"
echo "   ✅ No 404 errors for uploadInvoices"
echo ""
echo "📊 Backend Status Check:"
echo "   Backend API: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend is NOT running!"
    echo "   Start it with:"
    echo "   cd backend && source venv/bin/activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
fi

echo ""

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is running on port 3000"
else
    echo "❌ Frontend is NOT running!"
    echo "   Start it with:"
    echo "   cd finsentry-ui && npm run dev"
fi

echo ""
echo "🔍 If issues persist after hard refresh:"
echo "   1. Open browser DevTools (F12)"
echo "   2. Go to Application/Storage tab"
echo "   3. Click 'Clear storage'"
echo "   4. Click 'Clear site data'"
echo "   5. Refresh the page"
echo ""
echo "💡 The changes made:"
echo "   ✅ Fixed WebSocket: /ws/invoiceStatus → /ws/dashboard/metrics"
echo "   ✅ Fixed Upload: /uploadInvoices → /batches + /invoices/upload"
echo "   ✅ Updated API endpoints to match backend"
echo ""
