
---

## Chunk 3 — `Streaming-Events-Integration-&-State-Management.md`  
```markdown
# Streaming Events Integration & State Management for FinSentry Chatbot UI  
## 1. Purpose  
Define how real-time updates from backend will be streamed to frontend, how state is managed inside UI across chat + invoices + stages, how persistence and reconnection work, and how flags/timeout/error flows are handled.

## 2. Event Schema & Channels  
### 2.1 Event Structure  
```json
{
  "batchId": "BATCH-2025-11-07-001",
  "invoiceId": "INV-2025-1001",
  "agent": "Validator",
  "subtask": "Arithmetic Check",
  "status": "in_progress",
  "message": "Computing line item sum",
  "timestamp": "2025-11-07T12:05:23Z"
}
````

* `status` ∈ { “pending”, “in_progress”, “success”, “flagged”, “error” }
* `message` is optional, used if flagged or error.
* Events are published per-invoice per-subtask.

### 2.2 Channels

* WebSocket endpoint: `/ws/invoiceStatus` (prefer)
* Alternative SSE endpoint: `/events/invoiceStatus`
* Events may include batch–level summary:

```json
{
  "batchId":"BATCH-2025-11-07-001",
  "status":"completed",
  "completedCount":5,
  "flaggedCount":2
}
```

## 3. Frontend State Store

### 3.1 Global State

* `chatMessages: ChatMessage[]`
* `batches: Batch[]` where

```ts
interface Batch {
  batchId: string;
  uploadTimestamp: Date;
  invoiceIds: string[];
  completedCount: number;
  flaggedCount: number;
  status: 'in_progress'|'completed';
}
```

* `invoices: { [invoiceId: string]: InvoiceStatus }`

### 3.2 State Transitions

On event receipt:

* Find invoice by `invoiceId`, update `statuses[agent][subtask] = status`, `currentAgent = agent`, `currentSubtask = subtask`, `updatedAt = timestamp`.
* If status = `flagged` or `error`, add message to `flags[]`, set card highlight red.
* If all subtasks in agent success, mark agent as success. After all agents done, mark invoice overall “Completed”.

### 3.3 Timeout / Retry

* If no event for invoice in `in_progress` state after configured threshold (e.g., 2 min) -> set status `warning`, show “Processing delayed” and allow “Retry” button.
* If user clicks Retry, send API request to backend `POST /api/retryInvoice` and track.

## 4. Chat UI Integration

* When upload accepted, send chat message: “Your files have been uploaded → batch BATCH-2025-11-07-001”.
* As events come in, send messages like:

  > *[Extractor] Invoice INV-2025-1001 → OCR completed.*
  > *[Validator] Invoice INV-2025-1001 → Arithmetic mismatch flagged.*
* Use animated typing indicator while processing.

## 5. Persistence & Session Resume

* Store state in localStorage (or IndexedDB) so user reloads page and state persists.
* On reconnecting WebSocket after page refresh, re-subscribe and request current statuses via `GET /api/batchStatus?batchId=…`.
* On re-entry, reconstruct InvoiceCards statuses from store.

## 6. Error Handling & Edge Scenarios

* WebSocket disconnect: show snackbar “Connection lost – reconnecting…”. On reconnect, fetch snapshot.
* Backend returns unknown agent/subtask: log it, ignore or show generic.
* Large batch (>100): throttle UI updates, batch DOM operations (use requestAnimationFrame).
* Multi-browser/tab: state sync may conflict; treat each session separately unless you implement shared session ID.
* User uploads duplicate invoice-ID: highlight and treat as subtask of Validator “Duplicate Invoice Check”.

## 7. Performance Optimisations

* Virtualize long list of invoices (react-virtualized).
* Debounce chat message rendering if many events rapid-fire.
* Use WebSocket “rooms” by batch to minimise event traffic.
* Lazy-load detail panel contents when opened.

## 8. Summary

This chunk defines the streaming architecture, front-end state management, chat-integration with status updates, timeout and retry logic, and persistence. It enables your frontend developer (or Claude 4.5) to build a robust agentic UI for your invoice-processing multi-agent system.

---

```

---

### ✅ What to do next  
- Provide these three chunks to Claude 4.5 sequentially.  
- Once the model ingests them, ask it to generate the **React component skeleton**, **state management modules**, and **WebSocket integration code** for the UI.  
- Afterwards, you can request further chunks (e.g., “Design system & theming”, “Accessibility & i18n”, “Batch analytics dashboard”).

Let me know when you’d like **Chunk 4** and **Chunk 5** (covering design system + theming, and batch-analytics/dashboard).
::contentReference[oaicite:1]{index=1}
```
