# Project Memory: {{PROJECT_SLUG}}

## 1. Domain Inventory & Subsystem Boundaries
- `src/domains/<domain_a>/`: Owns [domain models, validation schemas, business logic, UI views, state][cite: 1].
  - `components/`: Internal domain-specific presentation components[cite: 1].
  - `composables/` (or `hooks/`): Domain state machines, reactive stores, and business workflows[cite: 1].
  - `models/`: TypeScript interfaces, database types, and schema validations[cite: 1].
  - `api/`: Domain HTTP client calls and mutation functions[cite: 1].
  - `tests/`: Co-located unit and integration tests[cite: 1].
  - `index.ts`: Strict public API export interface for cross-domain usage[cite: 1].
- `src/domains/<domain_b>/`: Owns [domain models, validation schemas, business logic, UI views, state][cite: 1].
- `src/shared/`: Domain-agnostic UI primitives (buttons, dialogs, inputs), base HTTP clients, and global utility helpers[cite: 1].

---

## 2. Domain State & Data Flow Architecture
- **State Ownership**: List stores (Pinia / Zustand / composables) and their owning domain boundaries[cite: 1].
- **Cross-Domain Contracts**: Explicit events, shared services, or public boundary imports between domains[cite: 1].
- **Async Data Lifecycle**: Conventions for handling the 5 UI states (Initial, Loading, Empty, Populated, Error) across domain views.

---

## 3. Libraries, Conventions & Domain Rules
- **Domain Invariants**: Non-obvious domain-specific constraints or business validation rules[cite: 1].
- **Routing & Navigation**: Route definitions and how they map to domain container views[cite: 1].
- **Third-Party & Framework Quirks**: Custom middleware, runtime flags, and library integration patterns[cite: 1].

---

## 4. Technical Debt & Implementation Deviations
- **Boundary Leaks**: Documented temporary workarounds or cross-domain coupling to revisit[cite: 1].
- **Logged Deviations**: Implementation choices logged in `implementation-notes.md`[cite: 1].