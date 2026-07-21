import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/landing',
      name: 'landing',
      component: () => import('@/pages/Landing.vue'),
      meta: { requiresGuest: true },
    },

    // ── Public ──────────────────────────────────────────────────────────
    {
      path: '/',
      component: () => import('@/layouts/AuthLayout.vue'),
      meta: { requiresGuest: true },
      children: [
        {
          path: '',
          redirect: { name: 'landing' },
        },
        {
          path: 'login',
          name: 'login',
          component: () => import('@/pages/Login.vue'),
        },
        {
          path: 'register',
          name: 'register',
          component: () => import('@/pages/Register.vue'),
        },
      ]
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
        {
          path: 'notifications',
          name: 'notifications',
          component: () => import('@/pages/Notifications.vue'),
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
              path: 'complaints/:id',
              name: 'admin-complaint-details',
              component: () => import('@/pages/administrator/AdminComplaintDetails.vue'),
              meta: { requiresAuth: true, role: 'administrator' },
            },
            {
              path: 'reports',
              name: 'admin-reports',
              component: () => import('@/pages/administrator/Reports.vue'),
              meta: { requiresAuth: true, role: 'administrator', adminLevel: 'system' },
            },
            {
              path: 'settings',
              name: 'admin-settings',
              component: () => import('@/pages/administrator/SystemSettings.vue'),
              meta: { requiresAuth: true, role: 'administrator', adminLevel: 'system' },
            },
            {
              path: 'municipal-administrators',
              name: 'admin-municipal-administrators',
              component: () => import('@/pages/administrator/MunicipalAdministrators.vue'),
              meta: { requiresAuth: true, role: 'administrator', adminLevel: 'system' },
            },
            {
              path: 'field-workers',
              name: 'admin-field-workers',
              component: () => import('@/pages/administrator/FieldWorkers.vue'),
              meta: { requiresAuth: true, role: 'administrator', adminLevel: 'municipal' },
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
            {
              path: 'assignments/:id',
              name: 'fieldworker-assignment-details',
              component: () => import('@/pages/fieldworker/AssignmentDetails.vue'),
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
