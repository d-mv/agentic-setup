# Component Standards & Interface Contract

## 1. Core Principles

* **Strict Scope**: Implement only what was explicitly requested; do not introduce unrequested architectural patterns, global catch-all solutions, or speculative abstractions without prior consent.


* **Strict Type Safety**: All props, emitted events, and component slots must be fully typed using TypeScript. The use of `any`, `unknown` without narrowing, or untyped catch-alls is prohibited.


* **No Uncontrolled Fallthrough**: Blind `$attrs` splatting or uncontrolled fallthrough overrides are strictly forbidden. Every accepted attribute must be explicitly declared and mapped.


* **TDD & Verification**: Write failing tests before writing component implementations. Run full static type checks (`vue-tsc -b` or `tsc --noEmit`) locally before pushing or deploying.



---

## 2. Vue Component Standards (`<script setup lang="ts">`)

### Syntax & Styling

* Use `<script setup lang="ts">` exclusively.
* Use scoped component CSS (`<style scoped>`). Never use TailwindCSS.


* Keep components stateless and modular; manage shared state via explicit Pinia stores or targeted composables.



### Props & Emits Definition

Always define explicit interfaces for `defineProps` and `defineEmits`:

```vue
<script setup lang="ts">
export interface UserCardProps {
  id: string;
  name: string;
  role: 'admin' | 'member' | 'guest';
  isActive?: boolean;
}

export interface UserCardEmits {
  (e: 'select', id: string): void;
  (e: 'delete', id: string): void;
}

const props = withDefaults(defineProps<UserCardProps>(), {
  isActive: false,
});

const emit = defineEmits<UserCardEmits>();
</script>

<template>
  <div class="user-card" :class="{ 'is-active': props.isActive }">
    <h3>{{ props.name }}</h3>
    <button type="button" @click="emit('select', props.id)">Select</button>
    <button type="button" @click="emit('delete', props.id)">Delete</button>
  </div>
</template>

<style scoped>
.user-card {
  border: 1px solid var(--border-color, #e2e8f0);
  padding: 1rem;
  border-radius: 8px;
}
.is-active {
  border-color: var(--primary-color, #3b82f6);
}
</style>

```

---

## 3. React Component Standards (TypeScript + CSS Modules)

### Syntax & Styling

* Use functional components with explicit TypeScript prop interfaces.


* Use Vanilla CSS Modules (`[name].module.css`). Never use TailwindCSS.


* Explicitly destructure allowed props; never use raw JSX spread attributes (`{...props}`) onto DOM elements without explicit filtering.

### Component Structure

```tsx
import React from 'react';
import styles from './UserCard.module.css';

export interface UserCardProps {
  id: string;
  name: string;
  role: 'admin' | 'member' | 'guest';
  isActive?: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export const UserCard: React.FC<UserCardProps> = ({
  id,
  name,
  role,
  isActive = false,
  onSelect,
  onDelete,
}) => {
  return (
    <div className={`${styles.card} ${isActive ? styles.isActive : ''}`}>
      <h3 className={styles.name}>{name} ({role})</h3>
      <button type="button" onClick={() => onSelect(id)}>Select</button>
      <button type="button" onClick={() => onDelete(id)}>Delete</button>
    </div>
  );
};

```

---

## 4. UI State Completeness Contract

Every data-driven or async component must explicitly handle and provide render coverage for the five UI lifecycle states:

1. **Initial / Idle**: Default resting state prior to interaction.
2. **Loading**: Pending state during async operations (with disabled triggers and accessible loading indicators).
3. **Empty**: Resolved state with zero data items, displaying clear empty feedback.
4. **Populated / Success**: Resolved state with valid data rendered.
5. **Error**: Handled failure state with human-readable error messages and retry mechanisms.