I’ll give you three chunk files right now (you can ask for more as needed). Each will include: UI architecture, data/state flows, component design, streaming/event model, visual status patterns, agent-wise sub-task breakdown, error/flag UI, accessibility, responsive design. These will be labelled so you can hand them in order.

---

## Chunk 1 — `UI-Architecture-&-Realtime-Status.md`

````markdown
# UI-Architecture & Realtime Status for FinSentry Agentic Chatbot  
## 1. Overview  
We are building a **chatbot-style UI** for your multi-agent system (Extractor, Validator, Anomaly, Learning, Coordinator). The UI must:  
- Accept invoice uploads (single or batch)  
- Show live status updates of each invoice as it flows through each agent and sub-task  
- Provide visual cues: green for success, yellow for in-progress, red for flagged/error  
- Support user questions and follow-ups (“Show me flagged invoices”, “What’s the status of invoice X?”)  
- Provide drill-down detail for each invoice and each agent stage  

## 2. Architecture Overview  
### 2.1 System Layers  
- **Chat Interface Layer**: conversation between user and agentic system.  
- **Status Visualization Layer**: below or within chat — shows per-invoice cards/list and live status.  
- **Detail Panel Layer**: when user clicks an invoice, show full detail (fields, line items, flags, logs).  
- **Backend Integration & Streaming Layer**: via WebSocket or Server-Sent Events (SSE) for real-time updates.  
- **State Management Layer**: maintains UI state of chat, invoices, statuses, filters, etc.  

### 2.2 Event/Streaming Flow  
- Backend (Coordinator Agent) emits events like:  
  ```json
  {
    "invoiceId":"INV-2025-1001",
    "agent":"Extractor",
    "subtask":"OCR Upload",
    "status":"in_progress",
    "timestamp":"2025-11-07T12:01:23Z"
  }
````

* Another event when subtask completes:

  ```json
  {
    "invoiceId":"INV-2025-1001",
    "agent":"Extractor",
    "subtask":"OCR Upload",
    "status":"success",
    "timestamp":"2025-11-07T12:01:45Z"
  }
  ```
* If anomaly:

  ```json
  {
    "invoiceId":"INV-2025-1001",
    "agent":"Validator",
    "subtask":"GSTIN Check",
    "status":"flagged",
    "message":"Vendor GSTIN invalid",
    "timestamp":"2025-11-07T12:02:10Z"
  }
  ```
* UI listens and updates the status cards accordingly.

### 2.3 State Model (simplified TypeScript)

```ts
interface InvoiceStatus {
  invoiceId: string;
  filename: string;
  currentAgent: string;
  currentSubtask: string;
  statuses: {
    [agent: string]: {
      [subtask: string]: 'pending'|'in_progress'|'success'|'flagged'|'error'
    }
  };
  flags: string[];
  updatedAt: Date;
}
interface ChatMessage {
  role: 'user'|'agent';
  content: string;
  timestamp: Date;
}
```

## 3. UI Components

* **UploadZone**: drag-and-drop or select files; displays “Upload X invoices” message.
* **ChatWindow**: shows user message, system responses, status cards.
* **InvoiceCard**: for each invoice shows filename, icon per agent stage (Extractor, Validator, Anomaly, Learning, Coordinator) with color indicators.
* **InvoiceDetailPanel**: opened on click, with tabs: Extraction, Validation, Anomaly, Logs.
* **FilterBar**: toggles “All”, “Flagged Only”, “Completed”, search by invoice ID.
* **StatusStreamIndicator**: top bar showing overall batch status (“3 of 5 done”, “2 flagged”, spinner).
* **ActionButtons**: when flag occurs – “Accept”, “Send for Manual Review”, “Reject”.

## 4. Visual Status Pattern

| Status      | Color  | Icon         |
| ----------- | ------ | ------------ |
| pending     | Grey   | ⏳            |
| in_progress | Yellow | 🔄 (spinner) |
| success     | Green  | ✅            |
| flagged     | Red    | ⚠️           |
| error       | Red    | ❌            |

Subtasks: represent each agent inside the card with icon and colored dot/label.

## 5. Responsive & Accessibility

* Mobile: single-column chat interface, invoice cards collapse, detail panel full-screen.
* Screen reader: use `aria-live="polite"` for status messages; ensure color variables not sole signal.
* Keyboard nav: tab order through upload, message input, InvoiceCard list, filter.
* High-contrast mode.

## 6. Real-time UX Details

* On upload, immediately send chat message: “Uploading 4 invoices …” and show loader.
* Streaming messages: programmatically update chat as events arrive (“Invoice X → Extractor started”, “Invoice X → Extractor completed”).
* For each invoice card, animate stage transitions (fade in at success, blink at flag).
* Batch summary updates live: “2 flagged, 3 completed, 1 in-progress”.
* If no event received for invoice > defined timeout (e.g., 2 minutes), show yellow alert “Waiting for processing…” with retry option.

## 7. Agent-wise Subtask Breakdown

Each of your 5 agents may have internal subtasks; we will reflect these in UI.

### Extractor Agent

* Subtasks: File upload receipt → OCR/Document AI call → Field extraction → Table extraction → Post-process & clean
* UI: show icons/text under Extractor stage: “OCR”, “Field parse”, “Table parse”.

### Validator Agent

* Subtasks: GSTIN validation → Arithmetic check → HSN rate check → Duplicate invoice check
* UI: under Validator stage show these subtasks status. If one fails: flag.

### Anomaly Agent

* Subtasks: Duplicate detection ↔ Market price compare ↔ Risk scoring ↔ Explanation generation
* UI: show subtasks similarly; provide link ‘View what flagged’.

### Learning Agent

* Subtasks: Feedback ingestion ↔ Model retrain ↔ Threshold adjustment ↔ Deploy update
* For UI session: often passive; show “Model update pending” or “Learning complete”.

### Coordinator Agent

* Subtasks: Workflow orchestration ↔ Event routing ↔ State tracking ↔ Audit log persist
* UI: show this final stage — on success show “Workflow Completed”, on error show “Workflow error – see logs”.

## 8. Flag/Alert Handling

* When `status === flagged`:

  * Change invoice card stage color red.
  * Display a modal or message bubble: “Invoice INV-### flagged for reason: …” with action buttons.
  * Tag card with “FLAGGED” badge.
* Yellow for warning (non-critical issue).
* Provide history link to view logs for flagged reason.

## 9. Batch & Back-Navigation

* Show batches by upload timestamp; allow collapse/expand.
* Provide “Go back to chat input” to ask follow-up queries.
* Maintain session context so chat remains linked to batch and invoices.

## 10. Performance & Scalability Considerations

* Use virtualization for large invoice lists (100+).
* Use WebSocket with segmented channels: `invoice:<id>` vs `batch:<batchId>` to limit updates.
* Debounce UI updates if many events per second.
* Limit attachments size and show progress bar.

## 11. Summary

This chunk outlines the UI architecture, real-time streaming status model, component breakdown, visual design, agent/ subtask mapping, and UX flows of your agentic invoice chatbot system. Next chunks will deep-dive each agent’s UI workflow and specific requirement for each.

---

````

