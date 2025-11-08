---

## Chunk 2 — `Agent-Stage-Workflows-UI.md`  
```markdown
# Agent Stage Workflows & UI Representation  
## 1. Purpose  
Provide detailed UI-flow definitions for each of the five agents: how they appear in the UI, what subtasks we display, how live status updates map to UI elements, how flags/errors show up, how user interacts.

---

## 2. Extractor Agent UI Flow  
### Appearance in UI  
- InvoiceCard stage icon labelled “Extractor”.  
- Under it, expandable submenu of subtasks:  
  - Upload Received  
  - OCR Processing  
  - Field Extraction  
  - Table Extraction  
  - Post-process Clean  

### Live Status Updates Example  
- Event: `invoiceId=INV-1001`, agent=Extractor, subtask=OCR Processing, status=in_progress → show spinner yellow next to “OCR Processing”.  
- Event: status=success → green check.  
- Failure: status=flagged/error → red icon and message “OCR failed: image too low resolution”.

### UI Representation  
```text
Extractor • 🔄  
  Upload Received ✅  
  OCR Processing 🔄  
  Field Extraction ✅  
  Table Extraction ✅  
  Post-process Clean ✅  
````

* Use indentation or accordion style within card or detail panel.

### Edge Cases

* No tables detected → show warning “No line items found”.
* Large PDF (multiple pages) → show “Page X of Y processed”.
* Unsupported format → immediately `error` with message “File type not supported”.

---

## 3. Validator Agent UI Flow

### Subtasks

* Vendor GSTIN Validation
* Arithmetic Check (sum of line items vs invoice total)
* HSN Rate Compliance
* Duplicate Invoice Check

### Live UI Example

```text
Validator • ✅  
  Vendor GSTIN Validation ✅  
  Arithmetic Check ⚠️ (line sum ≠ invoice total)  
  HSN Rate Compliance ✅  
  Duplicate Invoice Check ✅  
```

* If arithmetic fails, highlight subtask in yellow or red depending on threshold.

### Flag Handling

When GSTIN invalid: stage turns red; message bubble appears.
When arithmetic mismatch > 1%, stage yellow warning; user may choose to continue.

---

## 4. Anomaly Agent UI Flow

### Subtasks

* Duplicate Detection
* Market Price Benchmark
* Risk Score Generation
* Explanation Generation

### UI Example

```text
Anomaly • ⚠️  
  Duplicate Detection ✅  
  Market Price Benchmark 🔄  
  Risk Score Generation ✅  
  Explanation Generation ✅  
```

* Market price benchmark may take longer → spinner.
* Show risk score value (e.g., 0.87) and badge: “High Risk”.

### Visualisation

* Provide mini-chart or gauge for risk score.
* Flag: “Unit price 45% above benchmark”.

---

## 5. Learning Agent UI Flow

### Subtasks

* Feedback Collection
* Model Retrain
* Threshold Adjustment
* Deployment

### UI Example

```text
Learning • ✅  
  Feedback Collection ✅  
  Model Retrain 🔄  
  Threshold Adjustment ✅  
  Deployment ✅  
```

* Typically background; UI may show “Model updating…” then “Model version v2.3 deployed”.
* No invoices are stuck at this stage by user; but system monitoring shows this.

---

## 6. Coordinator Agent UI Flow

### Subtasks

* Workflow Orchestration
* Event Routing
* State Tracking
* Audit Log Persist

### UI Example

```text
Coordinator • ✅  
  Workflow Orchestration ✅  
  Event Routing ✅  
  State Tracking ✅  
  Audit Log Persist ✅  
```

* The final step: once this agent completes for invoice, the card moves to “Completed” state (green overall badge).
* If any stage failed earlier, Coordinator shows “Workflow ended with error”.

---

## 7. Visual Mapping Summary

```
InvoiceCard:
[ ICON ]  Invoice ID: INV-2025-1001  
  Stages: Extractor ✅ | Validator ⚠️ | Anomaly ✅ | Learning ✅ | Coordinator ✅  
  Flag: Arithmetic mismatch (yellow)
```

* Card shows list of stage icons; green/yellow/red.
* On click expands to detail panel.

---

## 8. Batch-Level UI Behaviour

* On uploading batch of N invoices: show “Batch X – 5 invoices” card.
* Expandable list of InvoiceCards beneath.
* Show batch progress bar or spinner: “3/5 done”.
* At end show summary: “2 flagged, 3 completed” with colour summary.

---

## 9. User Queries & Chat Integration

* User can ask: “What invoices are flagged?” → bot replies with list:

  > *Here are flagged invoices: INV-2025-1001 (Arithmetic mismatch), INV-2025-1004 (Duplicate).*
* UI then highlights those cards in red and optionally scrolls to them.

---

## 10. Summary

This chunk detailed UI flows for each of the 5 agents, their subtasks, live status representation, and UI mapping. The next chunk will deep-dive on **event schema, backend-frontend integration, error/timeout handling, and state persistence** for the UI side.

---

````
