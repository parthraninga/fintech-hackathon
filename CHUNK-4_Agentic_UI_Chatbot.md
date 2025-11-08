Great — here are **Chunk 4 and Chunk 5** of the detailed `.md` files for your agentic UI chatbot front-end. These extend the earlier chunks and include ultra-pro multilevel detail on design system & theming (Chunk 4) and batch analytics/dashboard integration (Chunk 5). You can feed them sequentially to your Claude 4.5 model.

---

## Chunk 4 — `Design-System-&-Theming.md`

````markdown
# Design System & Theming for FinSentry Agentic Chatbot UI  
## 1. Purpose  
Define a cohesive design system for the chatbot UI that ensures visual consistency, accessibility, scalable components, theming (light/dark), and brand alignment. This will be used by front-end developers and your Claude 4.5 prompt to generate components and code.

---

## 2. Design Language & Principles  
### 2.1 Core Design Principles  
- **Clarity & feedback**: Visual cues (colors, icons, motion) must clearly convey status (in-progress, success, flagged, error).  
- **Consistency**: Spacing, typography, iconography, component states must follow a unified system.  
- **Accessibility**: Color choices must work in high-contrast; use icons + text for status; keyboard navigation, screen reader announcements.  
- **Scalability & responsiveness**: Component system supports mobile, tablet, desktop; supports dark/light mode.  
- **Agentic identity**: The UI conveys that the system is working for the user (multi-agent orchestration) — use subtle animations and status flows to reinforce transparency.

### 2.2 Theme: Light & Dark  
Define two themes: Light (default) and Dark mode. Both use the same design tokens (colors, typography) but inverted backgrounds.

#### Colors (status palette)  
- Success (Green): `#28a745`  
- In-Progress (Yellow): `#ffc107`  
- Flagged/Warning (Orange): `#fd7e14`  
- Error/Failure (Red): `#dc3545`  
- Neutral/Pending (Gray): `#6c757d`  
Use brand primary colour for chat bubbles and action buttons.  
Use background white (light) or `#121212` (dark). Use surface cards with subtle shadows/contrast.

#### Typography  
- Base font: `Inter, sans-serif` (modern, readable)  
- Sizes:  
  - H1: 32px / 2rem  
  - H2: 24px / 1.5rem  
  - Body: 16px / 1rem  
  - Small text: 14px / 0.875rem  
- Line height: 1.5 for body.  
- Use font weights: Regular (400), Medium (500), Bold (700).

#### Spacing / Layout tokens  
- Small: 4px  
- Medium: 8px  
- Large: 16px  
- Extra-Large: 24px  
Use spacing tokens consistently for padding/margins.

#### Iconography  
- Use a consistent icon set (e.g., Material Icons or custom SVGs) for status:  
  - Spinner, Checkmark, Warning triangle, Error cross  
- For agent stages: use minimalist icons (e.g., gear for Coordinator, magnifier for Extractor, shield for Validator, chart/radar for Anomaly, brain for Learning).

#### Motion / Animation  
- Provide subtle transitions for status updates (fade in/out, scale up icons).  
- Use spinner animations for “in-progress”.  
- On stage complete: quick check-mark animation.  
- Do not over-animate — maintain professionalism and not distraction.

---

## 3. Component Library Structure  
### 3.1 Core Components  
- **Button**: variants: primary, secondary, danger, neutral; states: hover, active, disabled.  
- **Card**: reusable surface for InvoiceCard, batch summary, dashboard widgets.  
- **Badge**: status badge (success, flagged, pending).  
- **Spinner / Loader**: for asynchronous operations.  
- **ChatBubble**: user vs agent message styling.  
- **UploadDropzone**: file drag/drop component with batch upload support.  
- **Tabs**: for detail panels (Extraction/Validation/Anomaly/Logs).  
- **Table**: for line items, flagged listings.  
- **Icon**: status icon component with accessible label.  
- **Modal / Drawer**: for invoice detail panel on mobile/desktop.  
- **Toast / Snackbar**: transient messages (connection lost, retry, upload success).

### 3.2 Agent-Stage Components  
- **StageIndicator**: horizontal list inside InvoiceCard showing each agent (Extractor, Validator, Anomaly, Learning, Coordinator) with status icon and label.  
- **SubtaskAccordion**: expands to show subtasks inside an agent stage (e.g., OCR, GST check).  
- **FlagBanner**: red banner component with message and actions (Accept, Manual Review).

### 3.3 Theme Provider & Tokens  
- Use a ThemeProvider (e.g., styled-components, Chakra UI) with tokens: `colors`, `fontSizes`, `space`, `radii`, `shadows`.  
- Provide `useTheme()` hook for components to pull tokens.  
- Provide toggler to switch light/dark mode and persist preference (localStorage or user setting).

### 3.4 Utility Styles  
- `.visually-hidden` for screen reader only text.  
- `.status-success`, `.status-warning`, `.status-error` CSS classes referencing the tokens.  
- Responsive utility classes: `.sm:hidden`, `.md:flex`, etc.

---

## 4. Design System Documentation & Variant Guidelines  
- Document each component with its props, variant examples, accessibility notes.  
- Provide Figma (or other tool) library for design hand-off (see figma templates gallery). ([turn0search14])  
- Badge habits: success green should not rely only on colour (add icon + text).  
- Provide states for loading, disabled, error.  
- Provide spacing guidelines: e.g., between chat messages, between invoice cards, between detail panel elements.

---

## 5. Theming & Brand Identity  
- Logo should appear in chat header.  
- Use brand accent colour (e.g., `#0066ff`) for primary actions.  
- Use rounded corners (radius 8px) for cards and buttons.  
- Provide a “dark mode” toggle with labelled icon (moon/sun).  
- Use shadow: `box-shadow: 0px 1px 4px rgba(0,0,0,0.1)` on cards/light and `0px 1px 4px rgba(0,0,0,0.5)` on dark.

---

## 6. Accessibility & Internationalization  
- Provide `aria-live="assertive"` on live status updates to announce to screen readers.  
- Ensure color contrast ratio meets WCAG AA (minimum 4.5:1).  
- Provide high-contrast mode via CSS variables.  
- Support keyboard navigation throughout chat, upload, cards, filters.  
- Use semantic HTML (`<button>`, `<dialog>`, `<table>`) and meaningful `alt` text.  
- Support right-to-left (RTL) languages if needed (use `dir="rtl"`).  
- Provide `lang` attribute and locale support for dates, numbers, currency formatting.

---

## 7. Dark / Light Mode Usage Patterns  
- Light mode: background white, text dark (`#111111`).  
- Dark mode: background `#121212`, text light (`#e0e0e0`).  
- Maintain same spacing and component structure across modes.  
- Use `prefers-color-scheme` CSS feature to default.  
- Provide toggle for user override.  
- Change colors of status badges accordingly (green, yellow, red remain same hues but ensure contrast on dark).

---

## 8. Example Design Spec for InvoiceCard Component  
**Props**:  
```ts
type InvoiceCardProps = {
  invoiceId: string;
  filename: string;
  statuses: Record<string, Record<string, StageStatus>>;
  flags?: string[];
  onClick: (invoiceId:string) => void;
};
````

**Structure**:

```
Card
  Header: [Icon] invoiceId – filename
  StatusBar: [Extractor icon/status] [Validator icon/status] [Anomaly icon/status] [Learning icon/status] [Coordinator icon/status]
  Footer: 
    If flags exist → FlagBanner with message and action buttons
    Else summary text: “Completed” or “In progress”
```

**Variants**:

* Small size: card for mobile
* Expanded: show subtasks under each stage (accordion)
  **ARIA**: role="button" with aria-label “View invoice INV-1001 details”.

---

## 9. Summary

This document defines the design system and theming needed to build the front-end of your agentic invoice chat system. With these tokens, components, accessibility guidelines, and theme structure, your Claude 4.5 model or frontend engineer will have a strong foundation for building a beautiful, professional UI.
Next chunk (Chunk 5) delves into analytics and batch dashboard.

---

````

