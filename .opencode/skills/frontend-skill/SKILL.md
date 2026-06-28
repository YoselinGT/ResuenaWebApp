---
name: frontend-web-skill
description: >
  Experto en desarrollo frontend web de alto impacto visual: interfaces elegantes, responsivas,
  animadas y con la mejor experiencia de usuario. Activar este skill para: crear componentes
  React/Next.js/Vue, diseñar dashboards, landing pages, formularios, tablas de datos, modales,
  vistas de detalle, sistemas de design tokens, implementar animaciones, responsive design,
  dark mode, accesibilidad, code splitting, lazy loading, SSR/SSG, GraphQL client (Apollo/urql),
  gestión de estado (Zustand/Redux/Pinia), service workers/PWA, o cualquier interfaz de usuario web.
  También activar ante: "pantalla", "vista", "componente", "UI", "UX", "diseño", "estilo",
  "animación", "responsive", "móvil", "dashboard", "formulario", "tabla", "card", "modal",
  "colores", "tipografía", "tema", "palette", "web", "React", "Next.js", "Vue", "Nuxt",
  "SSR", "SSG", "code splitting", "lazy load", "Apollo Client", "GraphQL", "state management".
  NOTA: Para mobile nativo, usar frontend-mobile-skill. Para GraphQL API backend, usar api-graphql-skill.
---

# Frontend Skill — Interfaces Elegantes de Alto Impacto

Eres un Frontend Architect + UI Designer senior. Tu norte: **interfaces que enamoran al usuario
y son un placer de usar**. Cada pixel importa. La funcionalidad nunca sacrifica la estética.

---

## Protocolo de Onboarding (Proyecto Nuevo)

Antes de generar la **primera** vista de un proyecto, siempre hacer estas preguntas:

### Bloque 1 — Identidad Visual
1. ¿Tienen logo o identidad gráfica existente?
2. ¿Tienen paleta de colores definida o URL de referencia?
   - **URL de referencia** (sitio web, Figma, guía de marca) → extraer paleta desde ahí
   - **Colores específicos** (hex, RGB, nombre) → usar directamente
   - **Sin paleta** → sugerir 3 opciones con preview según el tono elegido
3. ¿Tono del producto? → opciones:
   - **Corporativo/Profesional** (azules, grises, minimalismo, tipografía sans)
   - **Moderno/Tech** (oscuro, gradientes sutiles, tipografía monoespaciada en acentos)
   - **Cálido/Humano** (neutrales cálidos, orgánico, accesible, bordes suaves)
   - **Luxe/Premium** (negro profundo + dorado/plata, serif display, espaciado generoso, glassmorphism)

### Bloque 2 — Audiencia y Contexto
4. ¿Quién usa la plataforma? → (internos empresa / clientes finales / técnicos / mixto)
5. ¿Dispositivo dominante? → (desktop 80% / mobile-first / parity)
6. ¿Manejo de datos sensibles? → (afecta densidad de información y confirmaciones)
7. ¿Es un dashboard con métricas/gráficas? → (activar patrones de data viz y drill-down)

### Bloque 3 — Preferencias Técnicas
8. ¿Framework frontend? → React/Next.js · Vue/Nuxt · Angular (afecta el código generado)
9. ¿Sistema de estilos existente? → Tailwind / CSS Modules / Styled Components / Material UI / ninguno
10. ¿Librería de gráficas preferida? → Recharts / Chart.js / Tremor / Apex Charts / D3 / ninguna

> Guardar respuestas en `references/brand-config.md` para que todas las vistas sean consistentes.

---

## Sistema de Design Tokens (plantilla base)

```css
/* tokens/design-tokens.css — fuente única de verdad visual */
:root {
  /* === Colores de Marca === */
  --color-primary-50:  #eff6ff;
  --color-primary-500: #3b82f6;   /* Principal */
  --color-primary-600: #2563eb;   /* Hover */
  --color-primary-900: #1e3a8a;   /* Dark variant */

  --color-accent-500:  #8b5cf6;   /* Acento / CTAs secundarios */
  --color-success:     #22c55e;
  --color-warning:     #f59e0b;
  --color-danger:      #ef4444;

  /* === Neutros === */
  --color-surface:     #ffffff;
  --color-surface-2:   #f8fafc;
  --color-border:      #e2e8f0;
  --color-text:        #0f172a;
  --color-text-muted:  #64748b;

  /* === Tipografía === */
  --font-sans:    'Inter', system-ui, sans-serif;
  --font-mono:    'JetBrains Mono', monospace;
  --font-display: 'Cal Sans', 'Inter', sans-serif;  /* Para headings grandes */

  /* === Espaciado === */
  --space-xs: 4px;   --space-sm: 8px;
  --space-md: 16px;  --space-lg: 24px;
  --space-xl: 32px;  --space-2xl: 48px;

  /* === Sombras === */
  --shadow-sm: 0 1px 3px rgba(0,0,0,.1), 0 1px 2px rgba(0,0,0,.06);
  --shadow-md: 0 4px 6px -1px rgba(0,0,0,.1), 0 2px 4px -1px rgba(0,0,0,.06);
  --shadow-lg: 0 10px 15px -3px rgba(0,0,0,.1), 0 4px 6px -2px rgba(0,0,0,.05);

  /* === Radios === */
  --radius-sm: 6px;  --radius-md: 10px;
  --radius-lg: 16px; --radius-full: 9999px;

  /* === Animaciones === */
  --ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-smooth:  cubic-bezier(0.25, 0.46, 0.45, 0.94);
  --duration-fast: 150ms;
  --duration-base: 250ms;
  --duration-slow: 400ms;
}

/* Dark mode automático */
@media (prefers-color-scheme: dark) {
  :root {
    --color-surface:    #0f172a;
    --color-surface-2:  #1e293b;
    --color-border:     #334155;
    --color-text:       #f1f5f9;
    --color-text-muted: #94a3b8;
  }
}
```

---

## Componentes Base — React/Next.js

### Botón con estados y animación
```tsx
// components/ui/Button.tsx
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

type ButtonProps = {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: React.ReactNode
} & React.ButtonHTMLAttributes<HTMLButtonElement>

export function Button({ variant = 'primary', size = 'md', loading, children, className, disabled, ...props }: ButtonProps) {
  const base = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
  
  const variants = {
    primary:   "bg-[var(--color-primary-500)] text-white hover:bg-[var(--color-primary-600)] shadow-sm hover:shadow-md focus-visible:ring-[var(--color-primary-500)]",
    secondary: "bg-[var(--color-surface-2)] text-[var(--color-text)] border border-[var(--color-border)] hover:bg-[var(--color-border)] focus-visible:ring-[var(--color-primary-500)]",
    ghost:     "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-text)]",
    danger:    "bg-[var(--color-danger)] text-white hover:opacity-90 shadow-sm"
  }
  
  const sizes = {
    sm: "h-8 px-3 text-sm gap-1.5",
    md: "h-10 px-4 text-sm gap-2",
    lg: "h-12 px-6 text-base gap-2"
  }

  return (
    <button className={cn(base, variants[variant], sizes[size], className)} disabled={disabled || loading} {...props}>
      {loading && <Loader2 className="animate-spin" size={size === 'sm' ? 14 : 16} />}
      {children}
    </button>
  )
}
```

### Tabla de datos con paginación y búsqueda
```tsx
// components/data/DataTable.tsx
'use client'
import { useState, useMemo } from 'react'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'

type Column<T> = {
  key: keyof T
  header: string
  render?: (value: T[keyof T], row: T) => React.ReactNode
  width?: string
}

type DataTableProps<T extends { id: string | number }> = {
  data: T[]
  columns: Column<T>[]
  pageSize?: number
  searchable?: boolean
  onRowClick?: (row: T) => void
}

export function DataTable<T extends { id: string | number }>({
  data, columns, pageSize = 20, searchable = true, onRowClick
}: DataTableProps<T>) {
  const [query, setQuery] = useState('')
  const [page, setPage] = useState(1)

  const filtered = useMemo(() => {
    if (!query) return data
    const q = query.toLowerCase()
    return data.filter(row =>
      Object.values(row).some(v => String(v).toLowerCase().includes(q))
    )
  }, [data, query])

  const totalPages = Math.ceil(filtered.length / pageSize)
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize)

  return (
    <div className="flex flex-col gap-4">
      {searchable && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)]" size={16} />
          <input
            className="w-full pl-9 pr-4 py-2 bg-[var(--color-surface-2)] border border-[var(--color-border)] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] transition-shadow"
            placeholder="Buscar..."
            value={query}
            onChange={e => { setQuery(e.target.value); setPage(1) }}
          />
        </div>
      )}
      
      <div className="overflow-x-auto rounded-xl border border-[var(--color-border)] shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-[var(--color-surface-2)] border-b border-[var(--color-border)]">
              {columns.map(col => (
                <th key={String(col.key)} className="px-4 py-3 text-left font-medium text-[var(--color-text-muted)] whitespace-nowrap" style={{ width: col.width }}>
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, i) => (
              <tr
                key={row.id}
                className={`border-b border-[var(--color-border)] last:border-0 transition-colors ${onRowClick ? 'cursor-pointer hover:bg-[var(--color-surface-2)]' : ''} ${i % 2 === 0 ? '' : 'bg-[var(--color-surface-2)]/40'}`}
                onClick={() => onRowClick?.(row)}
              >
                {columns.map(col => (
                  <td key={String(col.key)} className="px-4 py-3 text-[var(--color-text)]">
                    {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-[var(--color-text-muted)]">
          <span>{filtered.length} resultados</span>
          <div className="flex items-center gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 rounded-lg hover:bg-[var(--color-surface-2)] disabled:opacity-40 transition-colors">
              <ChevronLeft size={16} />
            </button>
            <span className="font-medium text-[var(--color-text)]">Página {page} de {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-1.5 rounded-lg hover:bg-[var(--color-surface-2)] disabled:opacity-40 transition-colors">
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
```

---

## Animaciones — Framer Motion (estándar del proyecto)

```tsx
// Entradas de página (staggered)
import { motion } from 'framer-motion'

const containerVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } }
}
const itemVariants = {
  hidden: { opacity: 0, y: 16 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] } }
}

// Usar en listas/cards:
<motion.ul variants={containerVariants} initial="hidden" animate="show">
  {items.map(item => (
    <motion.li key={item.id} variants={itemVariants}>{/* contenido */}</motion.li>
  ))}
</motion.ul>
```

---

## Responsive Design — Breakpoints

```
xs:   < 480px   → Mobile portrait
sm:   480–768px → Mobile landscape / tablet pequeña
md:   768–1024px→ Tablet
lg:   1024–1280px → Desktop normal
xl:   > 1280px  → Desktop amplio
```

**Regla mobile-first**: Diseñar primero para móvil, luego escalar hacia arriba con `md:`, `lg:`.

---

## Accesibilidad (A11y) — Obligatorio

- Todo elemento interactivo: `tabIndex`, `aria-label` o texto visible
- Contraste mínimo: 4.5:1 texto normal, 3:1 texto grande (WCAG AA)
- Nunca usar solo color para comunicar estado (agregar ícono o texto)
- Formularios: `<label>` asociado a cada `<input>` (no solo placeholder)
- Modales: `role="dialog"`, `aria-modal="true"`, focus trap

---

## Estados de UI (siempre implementar todos)

Para cada vista, implementar:
- **Loading**: Skeleton o spinner (no pantalla en blanco)
- **Empty**: Ilustración + mensaje + CTA
- **Error**: Mensaje claro + acción de reintento
- **Success**: Feedback positivo (toast / inline)

---

## Code Splitting y Lazy Loading

Optimizar bundle size dividiendo código por ruta y componente pesado.

```tsx
// React — lazy loading de rutas
import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Settings = lazy(() => import('./pages/Settings'))
const Reports = lazy(() => import('./pages/Reports'))

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/reports" element={<Reports />} />
      </Routes>
    </Suspense>
  )
}
```

```tsx
// Lazy loading de componentes pesados (charts, modales)
const ChartModal = lazy(() => import('./components/ChartModal'))
const DataTable = lazy(() => import('./components/DataTable'))

function DashboardPage() {
  const [showChart, setShowChart] = useState(false)

  return (
    <div>
      <button onClick={() => setShowChart(true)}>Ver gráfico</button>
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <ChartModal onClose={() => setShowChart(false)} />
        </Suspense>
      )}
    </div>
  )
}
```

### Next.js — Dynamic Imports

```tsx
// Next.js — import dinámico
import dynamic from 'next/dynamic'

const HeavyChart = dynamic(() => import('../components/HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false // Para componentes que solo usan client-side APIs
})

const DataTable = dynamic(() => import('../components/DataTable'), {
  loading: () => <TableSkeleton rows={10} />
})
```

---

## Server-Side Rendering (SSR) y Static Site Generation (SSG)

### Next.js — SSR para datos dinámicos

```tsx
// pages/record/[key].tsx — SSR
import { GetServerSideProps } from 'next'

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { key } = context.params
  const record = await recordService.findByKey(key)

  if (!record) {
    return { notFound: true }
  }

  return {
    props: {
      record: JSON.parse(JSON.stringify(record)) // Serialize Date
    }
  }
}
```

### Next.js — SSG para páginas estáticas

```tsx
// pages/landing/[slug].tsx — SSG con revalidate (ISR)
export const getStaticProps: GetStaticProps = async ({ params }) => {
  const landing = await landingService.findBySlug(params.slug)

  return {
    props: { landing },
    revalidate: 60 // Regenerar cada 60 segundos
  }
}

export async function getStaticPaths() {
  const landings = await landingService.getAllSlugs()
  return {
    paths: landings.map(l => ({ params: { slug: l.slug } })),
    fallback: 'blocking' // Generar bajo demanda si no existe
  }
}
```

### Vue — Nuxt SSR

```vue
<!-- pages/record/_key.vue -->
<script setup>
const route = useRoute()
const { data: record, pending, error } = await useFetch(
  `/api/records/${route.params.key}`
)
</script>
```

---

## GraphQL Client (Apollo Client / urql)

### Apollo Client — Setup y Queries

```tsx
// lib/apollo-client.ts
import { ApolloClient, InMemoryCache, createHttpLink } from '@apollo/client'

const httpLink = createHttpLink({
  uri: process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT
})

const cache = new InMemoryCache({
  typePolicies: {
    Record: {
      keyFields: ['key']
    },
    Query: {
      fields: {
        records: {
          keyArgs: ['filter'],
          merge(existing = [], incoming) {
            return [...existing, ...incoming]
          }
        }
      }
    }
  }
})

export const apolloClient = new ApolloClient({
  link: httpLink,
  cache,
  defaultOptions: {
    watchQuery: { fetchPolicy: 'cache-and-network' }
  }
})
```

### Apollo Client — Hooks

```tsx
// hooks/useRecord.ts
import { useQuery, useMutation, useSubscription } from '@apollo/client'
import { GET_RECORD, GET_RECORDS, CREATE_RECORD } from '../graphql/queries'

export function useRecord(key: string) {
  const { data, loading, error, refetch } = useQuery(GET_RECORD, {
    variables: { key },
    fetchPolicy: 'cache-and-network'
  })

  return {
    record: data?.record,
    loading,
    error,
    refetch
  }
}

export function useRecords(limit = 20) {
  const { data, loading, fetchMore } = useQuery(GET_RECORDS, {
    variables: { limit },
    notifyOnNetworkStatusChange: true
  })

  return {
    records: data?.records?.edges?.map(e => e.node) || [],
    hasMore: data?.records?.pageInfo?.hasNextPage,
    fetchMore
  }
}

// Mutation con actualización de cache
export function useCreateRecord() {
  const [createRecord, { loading }] = useMutation(CREATE_RECORD, {
    update: (cache, { data }) => {
      const existing = cache.readQuery({ query: GET_RECORDS })
      cache.writeQuery({
        query: GET_RECORDS,
        data: {
          records: {
            ...existing.records,
            edges: [{ node: data.createRecord, cursor: data.createRecord.key }, ...existing.records.edges]
          }
        }
      })
    }
  })

  return { createRecord, loading }
}
```

### urql — Alternativa más ligera

```tsx
// lib/urql-client.ts
import { createClient, cacheExchange, fetchExchange } from 'urql'

export const urqlClient = createClient({
  url: process.env.NEXT_PUBLIC_GRAPHQL_ENDPOINT,
  exchanges: [cacheExchange, fetchExchange]
})

// hooks/useRecords.ts
import { useQuery } from 'urql'

const GET_RECORDS = `
  query GetRecords($limit: Int!) {
    records(limit: $limit) {
      key
      payload
      createdAt
    }
  }
`

export function useRecords(limit = 20) {
  const [result] = useQuery({ query: GET_RECORDS, variables: { limit } })
  return { data: result.data?.records, fetching: result.fetching, error: result.error }
}
```

---

## Gestión de Estado (Zustand / Redux Toolkit / Pinia)

### Zustand — Estado simple y performante

```tsx
// store/useRecordStore.ts
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

interface RecordState {
  records: Map<string, Record>
  selectedKey: string | null
  isLoading: boolean
  error: string | null

  setRecords: (records: Record[]) => void
  selectRecord: (key: string | null) => void
  addRecord: (record: Record) => void
  updateRecord: (key: string, updates: Partial<Record>) => void
  removeRecord: (key: string) => void
}

export const useRecordStore = create<RecordState>()(
  immer((set) => ({
    records: new Map(),
    selectedKey: null,
    isLoading: false,
    error: null,

    setRecords: (records) => set((state) => {
      state.records = new Map(records.map(r => [r.key, r]))
    }),

    selectRecord: (key) => set((state) => {
      state.selectedKey = key
    }),

    addRecord: (record) => set((state) => {
      state.records.set(record.key, record)
    }),

    updateRecord: (key, updates) => set((state) => {
      const record = state.records.get(key)
      if (record) {
        state.records.set(key, { ...record, ...updates })
      }
    }),

    removeRecord: (key) => set((state) => {
      state.records.delete(key)
    })
  }))
)

// Uso en componente
function RecordList() {
  const { records, selectRecord } = useRecordStore()

  return (
    <ul>
      {Array.from(records.values()).map(record => (
        <li key={record.key} onClick={() => selectRecord(record.key)}>
          {record.key}
        </li>
      ))}
    </ul>
  )
}
```

### Redux Toolkit — Para estado complejo

```tsx
// store/recordsSlice.ts
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'

interface RecordsState {
  entities: Record[]
  selectedId: string | null
  loading: boolean
  error: string | null
}

const initialState: RecordsState = {
  entities: [],
  selectedId: null,
  loading: false,
  error: null
}

export const fetchRecords = createAsyncThunk(
  'records/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/records')
      if (!response.ok) throw new Error('Failed to fetch')
      return await response.json()
    } catch (err) {
      return rejectWithValue(err.message)
    }
  }
)

const recordsSlice = createSlice({
  name: 'records',
  initialState,
  reducers: {
    selectRecord: (state, action) => {
      state.selectedId = action.payload
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchRecords.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchRecords.fulfilled, (state, action) => {
        state.loading = false
        state.entities = action.payload
      })
      .addCase(fetchRecords.rejected, (state, action) => {
        state.loading = false
        state.error = action.payload as string
      })
  }
})

export const { selectRecord } = recordsSlice.actions
export default recordsSlice.reducer
```

### Pinia — Vue 3

```ts
// stores/recordStore.ts
import { defineStore } from 'pinia'

interface Record {
  key: string
  payload: Record<string, unknown>
  createdAt: string
}

export const useRecordStore = defineStore('records', {
  state: () => ({
    records: [] as Record[],
    selectedKey: null as string | null,
    loading: false
  }),

  getters: {
    selectedRecord: (state) =>
      state.records.find(r => r.key === state.selectedKey),

    recordsByKey: (state) => {
      const map = new Map<string, Record>()
      state.records.forEach(r => map.set(r.key, r))
      return map
    }
  },

  actions: {
    async fetchRecords() {
      this.loading = true
      try {
        const data = await $fetch('/api/records')
        this.records = data
      } finally {
        this.loading = false
      }
    },

    selectRecord(key: string | null) {
      this.selectedKey = key
    }
  }
})
```

---

## Service Workers y PWA

### Registro de Service Worker

```typescript
// lib/sw.ts
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js')
      console.log('SW registered:', registration.scope)

      registration.addEventListener('updatefound', () => {
        const newWorker = registration.installing
        newWorker?.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            // Nueva versión disponible
            console.log('New content available, please refresh.')
          }
        })
      })
    } catch (error) {
      console.error('SW registration failed:', error)
    }
  })
}
```

### Cache Strategy

```javascript
// public/sw.js — Service Worker con cache strategies

const CACHE_NAME = 'v1.0.0'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css'
]

// Install — cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  )
})

// Fetch — network first, fallback to cache
self.addEventListener('fetch', (event) => {
  const { request } = event

  // API calls — network only, no cache
  if (request.url.includes('/api/')) {
    event.respondWith(fetch(request))
    return
  }

  // Static assets — cache first
  event.respondWith(
    caches.match(request).then(response => {
      if (response) return response
      return fetch(request).then(networkResponse => {
        if (networkResponse.ok) {
          const clone = networkResponse.clone()
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone))
        }
        return networkResponse
      })
    })
  )
})

// Background sync para offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-records') {
    event.waitUntil(syncPendingRecords())
  }
})
```

### PWA Manifest

```json
// public/manifest.json
{
  "name": "Records App",
  "short_name": "Records",
  "description": "API REST Records Dashboard",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "orientation": "portrait-primary",
  "icons": [
    { "src": "/icons/icon-72.png", "sizes": "72x72", "type": "image/png" },
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

---

## Sistema de Tokens Luxe/Premium

Cuando el tono es **Luxe/Premium**, reemplazar los tokens base con este sistema:

```css
/* tokens/luxe-tokens.css — Identidad premium, oscura y editorial */
:root {
  /* === Paleta Noir + Dorado === */
  --color-primary-50:  #fdf8ed;
  --color-primary-100: #f7e8c0;
  --color-primary-300: #d4a843;
  --color-primary-500: #b8860b;   /* Gold — CTAs principales */
  --color-primary-600: #9a7209;   /* Gold hover */
  --color-primary-900: #3d2d04;   /* Gold profundo */

  --color-silver:      #c0c0c0;   /* Plata — elementos secundarios */
  --color-silver-muted:#8a8a8a;

  /* === Fondos Noir === */
  --color-bg-base:     #0a0a0a;   /* Negro absoluto */
  --color-bg-raised:   #111111;   /* Cards, modales */
  --color-bg-overlay:  #1a1a1a;   /* Hover, seleccionados */
  --color-bg-glass:    rgba(255, 255, 255, 0.04);  /* Glassmorphism */

  /* === Textos === */
  --color-text:        #f5f5f0;   /* Blanco cálido — texto principal */
  --color-text-muted:  #8a8a8a;   /* Gris — subtextos */
  --color-text-accent: var(--color-primary-300);  /* Gold — etiquetas, badges */

  /* === Borders === */
  --color-border:      rgba(212, 168, 67, 0.2);   /* Borde dorado sutil */
  --color-border-muted:rgba(255, 255, 255, 0.08); /* Borde glass */

  /* === Tipografía Premium === */
  --font-display: 'Playfair Display', 'DM Serif Display', Georgia, serif;  /* Títulos editoriales */
  --font-sans:    'Inter', 'Plus Jakarta Sans', system-ui, sans-serif;      /* Cuerpo */
  --font-mono:    'JetBrains Mono', 'Fira Code', monospace;                 /* Código/data */

  /* === Espaciado generoso (luxe respira) === */
  --space-xs:  6px;   --space-sm:  12px;
  --space-md:  20px;  --space-lg:  32px;
  --space-xl:  48px;  --space-2xl: 72px;  --space-3xl: 96px;

  /* === Sombras y Glow === */
  --shadow-gold-sm: 0 0 12px rgba(184, 134, 11, 0.25);
  --shadow-gold-md: 0 0 24px rgba(184, 134, 11, 0.35);
  --shadow-luxe:    0 20px 60px -10px rgba(0, 0, 0, 0.8);

  /* === Radios más conservadores (elegancia) === */
  --radius-sm: 4px;  --radius-md: 8px;  --radius-lg: 12px;

  /* === Animaciones premium (más lentas, más deliberadas) === */
  --ease-luxe:      cubic-bezier(0.16, 1, 0.3, 1);   /* Ease out expo */
  --ease-editorial: cubic-bezier(0.4, 0, 0.2, 1);    /* Material */
  --duration-luxe:  600ms;
  --duration-reveal:900ms;
}
```

### Glassmorphism Component

```tsx
// components/ui/GlassCard.tsx
export function GlassCard({ children, className, glow = false }) {
  return (
    <div
      className={cn(
        "relative rounded-lg overflow-hidden",
        "bg-[rgba(255,255,255,0.04)] backdrop-blur-xl",
        "border border-[rgba(212,168,67,0.2)]",
        "shadow-[0_20px_60px_-10px_rgba(0,0,0,0.8)]",
        glow && "shadow-[0_0_24px_rgba(184,134,11,0.35)]",
        className
      )}
    >
      {/* Borde superior dorado — detalle editorial */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[var(--color-primary-300)] to-transparent" />
      {children}
    </div>
  )
}
```

### Botón Luxe con Hover Dorado

```tsx
// components/ui/ButtonLuxe.tsx
export function ButtonLuxe({ children, variant = 'gold', ...props }) {
  const variants = {
    gold: `
      bg-gradient-to-r from-[#b8860b] to-[#d4a843]
      text-black font-semibold tracking-wider uppercase text-xs
      hover:from-[#d4a843] hover:to-[#f0c040]
      hover:shadow-[0_0_24px_rgba(184,134,11,0.5)]
      active:scale-[0.98] transition-all duration-300
    `,
    ghost: `
      border border-[rgba(212,168,67,0.4)] text-[var(--color-primary-300)]
      hover:border-[var(--color-primary-300)] hover:bg-[rgba(184,134,11,0.08)]
      hover:shadow-[0_0_12px_rgba(184,134,11,0.2)]
      transition-all duration-300
    `,
    dark: `
      bg-[var(--color-bg-raised)] text-[var(--color-text)]
      border border-[var(--color-border-muted)]
      hover:border-[var(--color-border)] hover:bg-[var(--color-bg-overlay)]
      transition-all duration-200
    `
  }

  return (
    <button
      className={cn(
        "px-6 py-3 rounded-md font-medium",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary-500)]",
        variants[variant]
      )}
      {...props}
    >
      {children}
    </button>
  )
}
```

---

## Animaciones Avanzadas — Alto Impacto Visual

### Reveal on Scroll (Intersection Observer)

```tsx
// hooks/useScrollReveal.ts
import { useEffect, useRef, useState } from 'react'

export function useScrollReveal(options = {}) {
  const ref = useRef<HTMLDivElement>(null)
  const [isVisible, setIsVisible] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsVisible(true)
        observer.unobserve(entry.target) // Animar solo una vez
      }
    }, { threshold: 0.15, ...options })

    if (ref.current) observer.observe(ref.current)
    return () => observer.disconnect()
  }, [])

  return { ref, isVisible }
}

// components/ui/RevealSection.tsx
export function RevealSection({ children, delay = 0, direction = 'up' }) {
  const { ref, isVisible } = useScrollReveal()

  const transforms = {
    up:    `translateY(${isVisible ? '0' : '40px'})`,
    left:  `translateX(${isVisible ? '0' : '-40px'})`,
    right: `translateX(${isVisible ? '0' : '40px'})`,
    fade:  'none'
  }

  return (
    <div
      ref={ref}
      style={{
        opacity: isVisible ? 1 : 0,
        transform: transforms[direction],
        transition: `opacity 700ms ease ${delay}ms, transform 700ms cubic-bezier(0.16,1,0.3,1) ${delay}ms`
      }}
    >
      {children}
    </div>
  )
}

// Uso con stagger
<div>
  {items.map((item, i) => (
    <RevealSection key={item.id} delay={i * 100}>
      <Card item={item} />
    </RevealSection>
  ))}
</div>
```

### Magnetic Button (Efecto táctil de lujo)

```tsx
// components/ui/MagneticButton.tsx
import { useRef } from 'react'

export function MagneticButton({ children, strength = 0.3, className }) {
  const buttonRef = useRef<HTMLButtonElement>(null)

  const handleMouseMove = (e: React.MouseEvent) => {
    const btn = buttonRef.current
    if (!btn) return
    const rect = btn.getBoundingClientRect()
    const x = (e.clientX - rect.left - rect.width / 2) * strength
    const y = (e.clientY - rect.top - rect.height / 2) * strength
    btn.style.transform = `translate(${x}px, ${y}px)`
  }

  const handleMouseLeave = () => {
    if (buttonRef.current)
      buttonRef.current.style.transform = 'translate(0, 0)'
  }

  return (
    <button
      ref={buttonRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={cn("transition-transform duration-300 ease-out", className)}
    >
      {children}
    </button>
  )
}
```

### Text Reveal (Efecto editorial de palabras)

```tsx
// components/animations/TextReveal.tsx
import { motion } from 'framer-motion'

export function TextReveal({ text, className }: { text: string; className?: string }) {
  const words = text.split(' ')

  return (
    <motion.span
      className={cn("inline-flex flex-wrap gap-x-[0.25em]", className)}
      initial="hidden"
      animate="show"
      variants={{ show: { transition: { staggerChildren: 0.1 } } }}
    >
      {words.map((word, i) => (
        <span key={i} className="overflow-hidden inline-block">
          <motion.span
            className="inline-block"
            variants={{
              hidden: { y: '110%', opacity: 0 },
              show:   { y: '0%',   opacity: 1, transition: { duration: 0.7, ease: [0.16, 1, 0.3, 1] } }
            }}
          >
            {word}
          </motion.span>
        </span>
      ))}
    </motion.span>
  )
}
```

### Counter Animation (KPIs y métricas)

```tsx
// components/animations/AnimatedCounter.tsx
import { useEffect, useRef } from 'react'
import { useScrollReveal } from '@/hooks/useScrollReveal'

export function AnimatedCounter({
  value,
  duration = 2000,
  prefix = '',
  suffix = '',
  decimals = 0
}: {
  value: number
  duration?: number
  prefix?: string
  suffix?: string
  decimals?: number
}) {
  const { ref, isVisible } = useScrollReveal()
  const countRef = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    if (!isVisible || !countRef.current) return
    const start = 0
    const startTime = performance.now()

    const update = (currentTime: number) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 4) // ease out quart
      const current = start + (value - start) * eased

      if (countRef.current) {
        countRef.current.textContent = `${prefix}${current.toFixed(decimals)}${suffix}`
      }

      if (progress < 1) requestAnimationFrame(update)
    }

    requestAnimationFrame(update)
  }, [isVisible, value, duration, prefix, suffix, decimals])

  return (
    <span ref={ref}>
      <span ref={countRef}>{prefix}0{suffix}</span>
    </span>
  )
}
```

---

## Data Visualization — Dashboards de Alto Impacto

### Setup Recharts (recomendado para React)

```bash
npm install recharts
# Complementos para dashboards premium:
npm install @tremor/react         # Componentes de dashboard listos
npm install date-fns              # Formateo de fechas en ejes
```

### KPI Card con Sparkline

```tsx
// components/dashboard/KPICard.tsx
import { LineChart, Line, ResponsiveContainer, Tooltip } from 'recharts'
import { TrendingUp, TrendingDown } from 'lucide-react'

interface KPICardProps {
  title: string
  value: string | number
  change: number          // % de cambio
  sparklineData: Array<{ value: number }>
  prefix?: string
  suffix?: string
}

export function KPICard({ title, value, change, sparklineData, prefix = '', suffix = '' }: KPICardProps) {
  const isPositive = change >= 0

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-5 flex flex-col gap-3">
      <p className="text-sm text-[var(--color-text-muted)] font-medium">{title}</p>

      <div className="flex items-end justify-between">
        <div>
          <AnimatedCounter
            value={typeof value === 'number' ? value : parseFloat(value)}
            prefix={prefix}
            suffix={suffix}
            className="text-3xl font-bold text-[var(--color-text)]"
          />
          <div className={cn(
            "flex items-center gap-1 mt-1 text-sm font-medium",
            isPositive ? "text-emerald-500" : "text-red-500"
          )}>
            {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            <span>{Math.abs(change).toFixed(1)}% vs mes anterior</span>
          </div>
        </div>

        <div className="w-28 h-14">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke={isPositive ? '#22c55e' : '#ef4444'}
                strokeWidth={2}
                dot={false}
              />
              <Tooltip
                contentStyle={{ display: 'none' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
```

### Gráfica de Área con Drill-Down

```tsx
// components/dashboard/DrillDownChart.tsx
'use client'
import { useState, useCallback } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Brush
} from 'recharts'
import { motion, AnimatePresence } from 'framer-motion'

type TimeGranularity = 'yearly' | 'monthly' | 'weekly' | 'daily'

interface DrillDownChartProps {
  data: Record<TimeGranularity, Array<{ label: string; value: number; details?: string }>>
  title: string
  color?: string
}

export function DrillDownChart({ data, title, color = '#3b82f6' }: DrillDownChartProps) {
  const [granularity, setGranularity] = useState<TimeGranularity>('monthly')
  const [selectedPoint, setSelectedPoint] = useState<string | null>(null)

  const handleBarClick = useCallback((payload: any) => {
    const next: Record<TimeGranularity, TimeGranularity | null> = {
      yearly: 'monthly',
      monthly: 'weekly',
      weekly: 'daily',
      daily: null
    }
    if (next[granularity]) {
      setGranularity(next[granularity]!)
      setSelectedPoint(payload?.activeLabel)
    }
  }, [granularity])

  const drillUpLabel: Record<TimeGranularity, string> = {
    yearly: '',
    monthly: 'Ver por año',
    weekly: 'Ver por mes',
    daily: 'Ver por semana'
  }

  const prevGranularity: Record<TimeGranularity, TimeGranularity | null> = {
    yearly: null,
    monthly: 'yearly',
    weekly: 'monthly',
    daily: 'weekly'
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null
    return (
      <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-3 shadow-lg">
        <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
        <p className="text-base font-bold text-[var(--color-text)]">
          {payload[0].value.toLocaleString()}
        </p>
        {prevGranularity[granularity] !== null && (
          <p className="text-xs text-[var(--color-primary-500)] mt-1">Click para ver detalle</p>
        )}
      </div>
    )
  }

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-semibold text-[var(--color-text)]">{title}</h3>
          <p className="text-sm text-[var(--color-text-muted)] capitalize">{granularity}</p>
        </div>
        <div className="flex items-center gap-2">
          {prevGranularity[granularity] && (
            <button
              onClick={() => setGranularity(prevGranularity[granularity]!)}
              className="text-xs text-[var(--color-primary-500)] hover:underline"
            >
              ← {drillUpLabel[granularity]}
            </button>
          )}
          {(['yearly', 'monthly', 'weekly', 'daily'] as TimeGranularity[]).map(g => (
            <button
              key={g}
              onClick={() => setGranularity(g)}
              className={cn(
                "px-2.5 py-1 text-xs rounded-md transition-colors",
                granularity === g
                  ? "bg-[var(--color-primary-500)] text-white"
                  : "text-[var(--color-text-muted)] hover:bg-[var(--color-surface-2)]"
              )}
            >
              {g.charAt(0).toUpperCase() + g.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={granularity}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.25 }}
          className="h-64"
        >
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data[granularity]}
              onClick={handleBarClick}
              style={{ cursor: prevGranularity[granularity] ? 'default' : 'pointer' }}
            >
              <defs>
                <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={color} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={color} stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" vertical={false} />
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2.5}
                fill={`url(#gradient-${color})`}
                activeDot={{ r: 5, fill: color }}
              />
              {data[granularity].length > 30 && <Brush dataKey="label" height={20} stroke="var(--color-border)" />}
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
```

### Tabla con Drill-Down y Ordenamiento

```tsx
// components/dashboard/DashboardTable.tsx — Tabla analítica expandible
'use client'
import { useState } from 'react'
import { ChevronDown, ChevronRight, ArrowUpDown } from 'lucide-react'

interface Row {
  id: string
  [key: string]: unknown
  children?: Row[]
}

export function DashboardTable<T extends Row>({
  data,
  columns,
  expandable = false
}: {
  data: T[]
  columns: Array<{ key: string; header: string; render?: (v: unknown, row: T) => React.ReactNode; align?: 'left' | 'right' | 'center' }>
  expandable?: boolean
}) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')

  const toggleExpand = (id: string) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const toggleSort = (key: string) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const sorted = [...data].sort((a, b) => {
    if (!sortKey) return 0
    const va = a[sortKey], vb = b[sortKey]
    const cmp = typeof va === 'number' && typeof vb === 'number'
      ? va - vb
      : String(va).localeCompare(String(vb))
    return sortDir === 'asc' ? cmp : -cmp
  })

  const renderRow = (row: T, depth = 0) => (
    <>
      <tr
        key={row.id}
        className="border-b border-[var(--color-border)] last:border-0 hover:bg-[var(--color-surface-2)] transition-colors"
      >
        {columns.map((col, i) => (
          <td
            key={col.key}
            className={cn(
              "px-4 py-3 text-sm text-[var(--color-text)]",
              col.align === 'right' && 'text-right tabular-nums',
              col.align === 'center' && 'text-center'
            )}
            style={i === 0 ? { paddingLeft: `${16 + depth * 20}px` } : {}}
          >
            {i === 0 && expandable && row.children?.length ? (
              <button
                onClick={() => toggleExpand(row.id)}
                className="inline-flex items-center gap-1.5"
              >
                {expanded.has(row.id)
                  ? <ChevronDown size={14} className="text-[var(--color-text-muted)]" />
                  : <ChevronRight size={14} className="text-[var(--color-text-muted)]" />
                }
                {col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—')}
              </button>
            ) : (
              col.render ? col.render(row[col.key], row) : String(row[col.key] ?? '—')
            )}
          </td>
        ))}
      </tr>
      {expanded.has(row.id) && row.children?.map(child => renderRow(child as T, depth + 1))}
    </>
  )

  return (
    <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[var(--color-surface-2)] border-b border-[var(--color-border)]">
            {columns.map(col => (
              <th
                key={col.key}
                className={cn(
                  "px-4 py-3 text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider cursor-pointer select-none",
                  col.align === 'right' && 'text-right'
                )}
                onClick={() => toggleSort(col.key)}
              >
                <span className="inline-flex items-center gap-1">
                  {col.header}
                  <ArrowUpDown size={12} className={sortKey === col.key ? 'text-[var(--color-primary-500)]' : 'opacity-40'} />
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map(row => renderRow(row))}
        </tbody>
      </table>
    </div>
  )
}
```

### Dashboard Layout — Grid Adaptativo

```tsx
// layouts/DashboardLayout.tsx
export function DashboardLayout({ kpis, chart, table, filters }) {
  return (
    <div className="min-h-screen bg-[var(--color-surface-2)] p-6">
      {/* Filtros */}
      <div className="mb-6 flex items-center gap-3 flex-wrap">
        {filters}
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {kpis}
      </div>

      {/* Gráfica principal */}
      <div className="mb-6">
        {chart}
      </div>

      {/* Tabla analítica */}
      <div>
        {table}
      </div>
    </div>
  )
}
```

---

## Micro-Interacciones — Detalles que Marcan la Diferencia

```tsx
// Skeleton loading (no pantallas en blanco)
export function SkeletonCard() {
  return (
    <div className="bg-[var(--color-surface)] rounded-xl p-5 animate-pulse">
      <div className="h-4 bg-[var(--color-border)] rounded w-1/3 mb-3" />
      <div className="h-8 bg-[var(--color-border)] rounded w-1/2 mb-2" />
      <div className="h-3 bg-[var(--color-border)] rounded w-1/4" />
    </div>
  )
}

// Toast con animación (sin librerías pesadas)
export function useToast() {
  const [toasts, setToasts] = useState<Array<{ id: string; message: string; type: 'success' | 'error' | 'info' }>>([])

  const show = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = crypto.randomUUID()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 4000)
  }

  const ToastContainer = () => (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map(toast => (
          <motion.div
            key={toast.id}
            initial={{ opacity: 0, x: 50, scale: 0.9 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: 50, scale: 0.9 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className={cn(
              "px-4 py-3 rounded-lg text-sm font-medium shadow-lg",
              toast.type === 'success' && "bg-emerald-600 text-white",
              toast.type === 'error'   && "bg-red-600 text-white",
              toast.type === 'info'    && "bg-[var(--color-surface)] text-[var(--color-text)] border border-[var(--color-border)]"
            )}
          >
            {toast.message}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  )

  return { show, ToastContainer }
}

// Input con label flotante (patrón premium)
export function FloatingInput({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  const [focused, setFocused] = useState(false)
  const [hasValue, setHasValue] = useState(false)

  return (
    <div className="relative">
      <input
        className={cn(
          "w-full px-4 pt-6 pb-2 text-sm rounded-lg",
          "bg-[var(--color-surface-2)] border transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)]",
          focused ? "border-[var(--color-primary-500)]" : "border-[var(--color-border)]"
        )}
        onFocus={() => setFocused(true)}
        onBlur={e => { setFocused(false); setHasValue(!!e.target.value) }}
        onChange={e => setHasValue(!!e.target.value)}
        {...props}
      />
      <label
        className={cn(
          "absolute left-4 transition-all duration-200 pointer-events-none",
          focused || hasValue
            ? "top-2 text-xs text-[var(--color-primary-500)]"
            : "top-1/2 -translate-y-1/2 text-sm text-[var(--color-text-muted)]"
        )}
      >
        {label}
      </label>
    </div>
  )
}
```

---

## Referencias Adicionales

- `references/brand-config.md` → Configuración de marca guardada del proyecto
- `references/component-catalog.md` → Inventario de componentes creados
- `references/animation-library.md` → Colección de animaciones reutilizables
- `references/dashboard-patterns.md` → Patrones de dashboard y drill-down
- `references/luxe-design-system.md` → Tokens y componentes premium
- `references/ssr-ssg-guide.md` → Cuándo usar SSR vs SSG
- `references/state-management.md` → Comparativa Zustand vs Redux vs Pinia
- `references/pwa-guide.md` → Setup completo de PWA
- `assets/icons/` → Iconos del proyecto

---

## Lecciones aprendidas (Portal Vendedores)

### Hydration mismatch por extensiones del navegador (gestores de contraseñas)

**Fecha:** 2026-05-20

**Problema que resuelve.** En Next.js App Router, las extensiones de gestor de contraseñas
(Norton, 1Password, LastPass, Bitwarden, Dashlane…) inyectan nodos (`<div>` con su icono de
autollenado) y/o reescriben atributos (`autocomplete`) dentro de los `<input>` **antes** de que
React hidrate. El DOM deja de coincidir con el HTML del servidor →
*"Hydration failed because the initial UI does not match what was rendered on the server"* /
*"Did not expect server HTML to contain a `<div>` in `<div>`"*. React aborta la hidratación y
re-renderiza todo el root en cliente.

**Diagnóstico rápido.**
- Reproduce en incógnito (sin extensiones): si desaparece → es la extensión, no el código.
- Verifica el HTML SSR real: `curl -s <url> | grep '<form'`. Si el servidor NO contiene el
  `<div>`/atributo en conflicto, lo inyecta la extensión en cliente.
- Solo afecta a `next dev` (overlay). En `next build && start` es un warning silencioso.

**DON'T**
- ❌ NO confíes en `suppressHydrationWarning`: solo cubre atributos/texto del **mismo** elemento,
  NO nodos `<div>` inyectados como hijos.
- ❌ NO dependas de `data-1p-ignore` / `data-lpignore` / `data-bwignore` / `data-form-type="other"`:
  varios gestores (p. ej. Norton) los ignoran.

**DO**
- ✅ Renderiza el formulario **solo en cliente** (tras la hidratación) con un gate `useMounted` +
  `ClientOnly`, mostrando un skeleton como `fallback`. Como el `<form>` no está en el HTML del
  servidor, ninguna extensión puede provocar mismatch.

```tsx
// hooks/useMounted.ts
export function useMounted() {
  const [m, setM] = useState(false);
  useEffect(() => setM(true), []);
  return m;
}

// components/ui/ClientOnly.tsx
export function ClientOnly({ children, fallback = null }) {
  return <>{useMounted() ? children : fallback}</>;
}

// uso — el <form> no se renderiza en SSR
<ClientOnly fallback={<FormSkeleton />}>
  <form>…inputs…</form>
</ClientOnly>
```

Verificación: `curl -s http://localhost:3000/login | grep -c '<form'` debe dar `0`.

### Tokens de tema vs. paleta hardcodeada (dark mode)
