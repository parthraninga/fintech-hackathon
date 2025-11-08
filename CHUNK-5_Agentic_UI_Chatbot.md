---

## Chunk 5 — `Batch-Analytics-&-Dashboard.md`  
```markdown
# Batch Analytics & Dashboard for FinSentry Agentic Chatbot  
## 1. Purpose  
Provide an advanced analytics dashboard layer that complements the chat UI: visualizing batch performance, flagged invoice statistics, agent stage throughput, anomaly rates, processing latency, model learning curves — enabling executive overview and operational visibility.

---

## 2. Key Metrics & KPIs  
Define metrics your dashboard should track:
- Total invoices processed (daily/weekly/monthly)  
- Flagged invoice count and rate (flags/invoices)  
- Throughput by agent stage (invoices/hour)  
- Average processing latency per invoice (end-to-end time)  
- Breakdown by agent: extraction time, validation time, anomaly detection time  
- Learning Agent model version, retrain count, feedback queue length  
- Vendor risk profile: number of flagged invoices by vendor  
- Duplicate invoice rate and top duplicate vendors  
- Market price deviation statistics (line items > X% deviation)  
- System health: queue length, worker count, error rate  

Dashboard design best practices: use visual hierarchy, consistent colour coding, and card layout. ([turn0search2], [turn0search4])

---

## 3. Dashboard Layout & Components  
### 3.1 Page Structure  
- **Header**: title (“FinSentry Dashboard”), date-picker for time range.  
- **Top KPI cards row**:  
  - Card: “Processed Invoices” – large number  
  - Card: “Flagged Rate” – % with sparkline  
  - Card: “Avg Latency” – time in seconds  
- **Agent Throughput Charts**: line chart showing throughput per stage over time.  
- **Flagged Trend**: bar chart monthly flagged count vs total.  
- **Vendor Risk Table**: table with vendor GSTIN, flagged count, risk score, view invoices link.  
- **Processing Latency Distribution**: histogram or box-plot of latency per invoice.  
- **Model Learning Panel**: display current model version (Learning Agent), feedback queue size, retrain count.  
- **Export/Filter Panel**: button to export CSV, filters by vendor, date range, status.

### 3.2 Visual Elements & Style  
- Use card-grid layout with consistent spacing.  
- Use colour palette: green (good), yellow/orange (warning), red (critical).  
- Provide “hover to reveal exact number” and tooltips.  
- Use animated transitions when data updates (live dashboard).  
- Provide loading skeletons while data fetches.  
- Use dark/light theme aligned with design system (Chunk 4).

---

## 4. Data Flow & Backend Integration  
- Frontend fetches from backend analytics endpoint: `/api/dashboard/metrics?from=…&to=…`.  
- Use WebSocket or SSE for live streaming of metrics (optional).  
- Backend aggregates from logs, database tables (e.g., `invoice_validations`, `gstin_cache`), and time-series store (Prometheus/Timescale).  
- Use caching and pagination for large datasets (vendor table).  
- Provide export API: `/api/dashboard/export/csv?filters=…`.

---

## 5. Batch UI Integration with Chat Interface  
- From chat UI, when batch completes, offer “View batch analytics” button.  
- Clicking opens dashboard layer with initial view for that batch.  
- Provide quick filters: “Flagged invoices in this batch”, “Top vendors flagged”.  
- Provide link back to chat: “Return to conversation”.

---

## 6. User Roles & Access  
- **End User**: can view chat UI + their batch analytics.  
- **Manager**: can view full dashboard, filter by multiple users, export data.  
- **Admin**: can view system health metrics (error rates, queue lengths).  
Ensure role-based access control applies.

---

## 7. Responsive & Mobile Considerations  
- KPI cards collapse into carousel on mobile.  
- Use vertical stack for charts.  
- Vendor table becomes expandable list.  
- Dashboard accessible from bottom nav in mobile view.

---

## 8. Edge Cases & Performance  
- Large date range (1 year) → fallback to aggregated data, show “Too many data points, summarizing”.  
- Live streaming pauses if browser tab inactive — show message “Live updates paused”.  
- Export large CSVs asynchronously — show progress and email when ready.  
- Data missing for period → show “No data available” card.  
- Latency outlier extreme values → cap scale and provide zoom-out option.

---

## 9. Summary  
This chunk outlines a full analytics/dashboard layer to complement the agentic chat UI, giving you live operational insights, batch-level visualisations, and executive metrics. With this, your frontend build and Claude 4.5 model will have detailed specifications for both conversation UI and dashboard analytics.

---
````

---
