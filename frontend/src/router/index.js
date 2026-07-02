import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ── Public ──────────────────────────────────────────────────────────
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/Login.vue'),
      meta: { requiresGuest: true },
    },

    // ── Shared (authenticated) ──────────────────────────────────────────
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard',
        },
        {
          path: 'dashboard',
          name: 'dashboard',
          component: () => import('@/pages/Dashboard.vue'),
          meta: { requiresAuth: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('@/pages/Profile.vue'),
          meta: { requiresAuth: true },
        },

        // ── Citizen ────────────────────────────────────────────────────
        {
          path: 'citizen',
          children: [
            {
              path: 'dashboard',
              name: 'citizen-dashboard',
              component: () => import('@/pages/citizen/CitizenDashboard.vue'),
              meta: { requiresAuth: true, role: 'citizen' },
            },
            {
              path: 'report',
              name: 'report-complaint',
              component: () => import('@/pages/citizen/ReportComplaint.vue'),
              meta: { requiresAuth: true, role: 'citizen' },
            },
            {
              path: 'track',
              name: 'track-complaint',
              component: () => import('@/pages/citizen/TrackComplaint.vue'),
              meta: { requiresAuth: true, role: 'citizen' },
            },
            {
              path: 'complaints/:id',
              name: 'complaint-details',
              component: () => import('@/pages/citizen/ComplaintDetails.vue'),
              meta: { requiresAuth: true, role: 'citizen' },
            },
          ],
        },

        // ── Administrator ──────────────────────────────────────────────
        {
          path: 'admin',
          children: [
            {
              path: 'dashboard',
              name: 'admin-dashboard',
              component: () => import('@/pages/administrator/AdministratorDashboard.vue'),
              meta: { requiresAuth: true, role: 'administrator' },
            },
            {
              path: 'reports',
              name: 'admin-reports',
              component: () => import('@/pages/administrator/Reports.vue'),
              meta: { requiresAuth: true, role: 'administrator', adminLevel: 'system' },
            },
          ],
        },

        // ── Field Worker ───────────────────────────────────────────────
        {
          path: 'fieldworker',
          children: [
            {
              path: 'dashboard',
              name: 'fieldworker-dashboard',
              component: () => import('@/pages/fieldworker/FieldWorkerDashboard.vue'),
              meta: { requiresAuth: true, role: 'field_worker' },
            },
          ],
        },
      ],
    },

    // ── 404 ─────────────────────────────────────────────────────────────
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/pages/NotFound.vue'),
    },
  ],
})

// ── Navigation Guards ────────────────────────────────────────────────────────

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  await authStore.hydrateSession()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next({ name: 'login', query: { redirect: to.fullPath } })
  }

  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    if (authStore.userRole === 'administrator') return next({ name: 'admin-dashboard' })
    if (authStore.userRole === 'citizen') return next({ name: 'citizen-dashboard' })
    if (authStore.userRole === 'field_worker') return next({ name: 'fieldworker-dashboard' })
    return next({ name: 'dashboard' })
  }

  if (to.meta.role && authStore.userRole !== to.meta.role) {
    return next({ name: 'dashboard' })
  }

  if (to.meta.adminLevel && authStore.adminLevel !== to.meta.adminLevel) {
    return next({ name: 'admin-dashboard' })
  }

  next()
})

export default router
