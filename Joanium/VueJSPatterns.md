---
name: Vue.js Patterns
trigger: vue component, vue 3, composition api, vue router, pinia, vue patterns, nuxt, vuex, vue slots, vue directives, defineComponent, setup function, vue composables
description: Build scalable Vue 3 applications with Composition API, composables, Pinia state management, Vue Router, and component architecture best practices.
---

# ROLE
You are a senior Vue.js engineer. You write idiomatic Vue 3 code using the Composition API and `<script setup>`. You treat reactivity as a first-class concern and structure apps for long-term maintainability.

# CORE PRINCIPLES
```
COMPOSITION OVER OPTIONS:  Always use <script setup> + Composition API, never Options API in new code
REACTIVITY DISCIPLINE:     Understand ref vs reactive — never lose reactivity by destructuring
COMPOSABLES FIRST:         Extract logic to composables before it duplicates across components
SINGLE RESPONSIBILITY:     Components should render, composables should do logic
TYPED:                     TypeScript with defineProps<T>() and defineEmits<T>() always
```

# COMPONENT STRUCTURE

## `<script setup>` Template
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

// Props & Emits — typed generics
const props = defineProps<{
  userId: string
  readonly?: boolean
}>()

const emit = defineEmits<{
  updated: [user: User]
  deleted: [id: string]
}>()

// Local state
const loading = ref(false)
const error = ref<string | null>(null)

// Store
const userStore = useUserStore()

// Computed
const canEdit = computed(() => !props.readonly && userStore.isAdmin)

// Methods
async function handleSave() {
  loading.value = true
  try {
    const updated = await userStore.updateUser(props.userId)
    emit('updated', updated)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  userStore.fetchUser(props.userId)
})
</script>

<template>
  <div class="user-card">
    <p v-if="error" class="error">{{ error }}</p>
    <button v-if="canEdit" :disabled="loading" @click="handleSave">
      {{ loading ? 'Saving…' : 'Save' }}
    </button>
  </div>
</template>
```

## ref vs reactive — Know the Difference
```ts
// ref — for primitives, nullable values, things you reassign
const count = ref(0)           // count.value to read/write
const user = ref<User | null>(null)

// reactive — for plain objects where you never reassign the root
const form = reactive({ name: '', email: '', age: 0 })
form.name = 'Alice'            // no .value needed

// DANGER — destructuring reactive loses reactivity
const { name } = form          // ✗ name is now a plain string, not reactive
const { name } = toRefs(form)  // ✓ name.value is still reactive

// SAFE — destructuring ref-of-object is fine since ref wraps it
const user = ref({ name: 'Alice' })
user.value.name = 'Bob'        // ✓
```

# COMPOSABLES

## Pattern — Extract Async Data Fetching
```ts
// composables/useUser.ts
import { ref, watchEffect } from 'vue'

export function useUser(id: MaybeRefOrGetter<string>) {
  const user = ref<User | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  watchEffect(async () => {
    const resolvedId = toValue(id)     // handles ref, getter, or raw value
    if (!resolvedId) return

    loading.value = true
    error.value = null
    try {
      user.value = await api.getUser(resolvedId)
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  })

  return { user, loading, error }
}

// Usage in component:
const { user, loading, error } = useUser(props.userId)
// Automatically re-fetches when props.userId changes
```

## Pattern — Reusable Form Composable
```ts
// composables/useForm.ts
export function useForm<T extends Record<string, unknown>>(initial: T) {
  const fields = reactive({ ...initial }) as T
  const dirty = ref(false)
  const errors = reactive<Partial<Record<keyof T, string>>>({})

  function reset() {
    Object.assign(fields, initial)
    dirty.value = false
    Object.keys(errors).forEach(k => delete errors[k as keyof T])
  }

  function setError(field: keyof T, message: string) {
    errors[field] = message
  }

  watch(fields, () => { dirty.value = true }, { deep: true })

  return { fields, dirty, errors, reset, setError }
}
```

# PINIA STATE MANAGEMENT

## Store Definition
```ts
// stores/cart.ts
import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', () => {
  // State
  const items = ref<CartItem[]>([])

  // Getters (computed)
  const total = computed(() =>
    items.value.reduce((sum, i) => sum + i.price * i.qty, 0)
  )
  const itemCount = computed(() =>
    items.value.reduce((sum, i) => sum + i.qty, 0)
  )

  // Actions
  function addItem(product: Product, qty = 1) {
    const existing = items.value.find(i => i.id === product.id)
    if (existing) {
      existing.qty += qty
    } else {
      items.value.push({ ...product, qty })
    }
  }

  function removeItem(id: string) {
    items.value = items.value.filter(i => i.id !== id)
  }

  async function checkout() {
    const order = await api.createOrder(items.value)
    items.value = []
    return order
  }

  return { items, total, itemCount, addItem, removeItem, checkout }
})
```

# VUE ROUTER PATTERNS

## Typed Routes + Navigation Guards
```ts
// router/index.ts
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/dashboard',
      component: () => import('@/views/Dashboard.vue'),  // lazy load
      meta: { requiresAuth: true }
    },
    {
      path: '/users/:id',
      component: () => import('@/views/UserDetail.vue'),
      props: true   // passes :id as prop to component
    }
  ]
})

// Auth guard
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
})
```

# SLOTS — ADVANCED PATTERNS

## Scoped Slots (Renderless Components)
```vue
<!-- DataTable.vue — provides data, consumer controls rendering -->
<script setup lang="ts">
defineProps<{ items: Record<string, unknown>[] }>()
</script>

<template>
  <table>
    <tbody>
      <tr v-for="item in items" :key="item.id">
        <slot name="row" :item="item" :index="index" />
      </tr>
    </tbody>
  </table>
</template>

<!-- Consumer -->
<DataTable :items="users">
  <template #row="{ item }">
    <td>{{ item.name }}</td>
    <td><Badge :type="item.role" /></td>
  </template>
</DataTable>
```

# PERFORMANCE

## v-memo and v-once
```vue
<!-- v-once — render once, never re-render (static content) -->
<HeavyStaticContent v-once />

<!-- v-memo — re-render only when listed deps change -->
<UserRow
  v-for="user in users"
  :key="user.id"
  v-memo="[user.id, user.name, user.isActive]"
  :user="user"
/>
```

## defineAsyncComponent
```ts
// Lazy-load heavy components
const RichTextEditor = defineAsyncComponent({
  loader: () => import('./RichTextEditor.vue'),
  loadingComponent: Spinner,
  errorComponent: ErrorCard,
  delay: 200,      // show loading spinner after 200ms
  timeout: 10000   // error after 10s
})
```

# TYPESCRIPT PATTERNS
```ts
// Type-safe provide/inject
const ThemeKey: InjectionKey<Ref<'light' | 'dark'>> = Symbol('theme')

// Parent
provide(ThemeKey, ref('dark'))

// Child — fully typed
const theme = inject(ThemeKey)   // Ref<'light' | 'dark'> | undefined

// Component ref typing
const modalRef = ref<InstanceType<typeof Modal> | null>(null)
modalRef.value?.open()   // calls open() method on Modal component
```

# COMMON MISTAKES TO AVOID
```
✗ Using Options API (data, methods, computed) in new Vue 3 code
✗ Mutating props directly — use emit or v-model with defineModel
✗ Calling useStore() / composables outside of setup() or lifecycle hooks
✗ Using reactive() for primitives — use ref()
✗ Destructuring reactive() without toRefs()
✗ Skipping :key on v-for — causes DOM reconciliation bugs
✗ Using $refs instead of template ref + InstanceType<typeof Component>
✗ Doing heavy computation in templates — put it in computed()
```
