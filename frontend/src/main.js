import './style.css'

import {
  getAccessToken,
  login,
  logout,
  apiFetch,
} from './api'

import { renderHome } from './pages/home'
import { renderQrScanner } from './pages/qrScanner'
import { renderPublicVerification } from './pages/publicVerification'
import { renderPublicCertificate } from './pages/publicCertificate'

import { renderApplications } from './pages/applications'
import { renderCertificates } from './pages/certificates'
import { renderDocuments } from './pages/documents'
import { renderInspections } from './pages/inspections'
import { renderInstruments } from './pages/instruments'
import { renderOfficerApplications } from './pages/officerApplications'
import { renderSearch } from './pages/search'

const app = document.querySelector('#app')

const path = window.location.pathname

/*
 * PUBLIC ROUTES
 *
 * These routes do not require authentication.
 */

if (path === '/' || path === '') {
  renderHome()
} else if (path === '/scan' || path === '/scan/') {
  renderQrScanner()
} else if (
  path.startsWith('/verify/certificate/')
) {
  const parts = path.split('/').filter(Boolean)

  if (parts[2]) {
    renderPublicCertificate(
      decodeURIComponent(parts[2])
    )
  } else {
    renderHome()
  }
} else if (path.startsWith('/verify/')) {
  const parts = path.split('/').filter(Boolean)

  if (parts[1]) {
    renderPublicVerification(
      decodeURIComponent(parts[1])
    )
  } else {
    renderHome()
  }
} else if (getAccessToken()) {
  renderPortal()
} else {
  renderLogin()
}

/*
 * LOGIN
 */

async function renderLogin() {
  app.innerHTML = `
    <div class="min-h-screen bg-slate-100">
      <div class="flex min-h-screen items-center justify-center px-6 py-10">

        <div class="w-full max-w-md border border-slate-200 bg-white">

          <div class="border-b border-slate-200 px-7 py-6">
            <div class="text-lg font-semibold text-slate-900">
              Legal Metrology Department
            </div>

            <div class="mt-1 text-sm text-slate-500">
              Digital Portal
            </div>
          </div>

          <form id="login-form" class="space-y-5 px-7 py-7">

            <div>
              <label class="label">
                Username
              </label>

              <input
                id="username"
                class="field mt-2"
                autocomplete="username"
                required
              />
            </div>

            <div>
              <label class="label">
                Password
              </label>

              <input
                id="password"
                type="password"
                class="field mt-2"
                autocomplete="current-password"
                required
              />
            </div>

            <div
              id="login-error"
              class="hidden border border-red-200 bg-red-50 p-3 text-sm text-red-700"
            ></div>

            <button
              id="login-button"
              type="submit"
              class="w-full bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
            >
              Sign In
            </button>

            <button
              id="public-portal"
              type="button"
              class="w-full border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Public Verification Portal
            </button>

          </form>

        </div>

      </div>
    </div>
  `

  document
    .querySelector('#public-portal')
    .addEventListener('click', () => {
      window.location.href = '/'
    })

  document
    .querySelector('#login-form')
    .addEventListener('submit', async (event) => {

      event.preventDefault()

      const button =
        document.querySelector('#login-button')

      const errorBox =
        document.querySelector('#login-error')

      button.disabled = true
      button.textContent = 'Signing in...'

      errorBox.classList.add('hidden')

      try {
        await login(
          document
            .querySelector('#username')
            .value
            .trim(),

          document
            .querySelector('#password')
            .value
        )

        await renderPortal()

      } catch (error) {

        errorBox.textContent =
          error.message

        errorBox.classList.remove('hidden')

      } finally {

        button.disabled = false
        button.textContent = 'Sign In'
      }
    })
}

/*
 * AUTHENTICATED PORTAL
 */

async function renderPortal() {

  let dashboard

  try {

    dashboard =
      await apiFetch(
        '/verification/dashboard/'
      )

  } catch (error) {

    logout()

    renderLogin()

    return
  }

  const role = dashboard.role

  const menu =
    getMenuForRole(role)

  app.innerHTML = `
    <div class="min-h-screen bg-slate-100">

      <header class="border-b border-slate-200 bg-white">

        <div class="flex h-16 items-center justify-between px-5">

          <div>

            <div class="text-base font-semibold text-slate-900">
              Legal Metrology Portal
            </div>

            <div class="text-xs text-slate-500">
              Government Digital Administration System
            </div>

          </div>

          <div class="flex items-center gap-4">

            <div class="hidden text-right sm:block">

              <div class="text-sm font-medium text-slate-900">
                ${escapeHtml(
                  dashboard.username || 'User'
                )}
              </div>

              <div class="text-xs text-slate-500">
                ${escapeHtml(role)}
              </div>

            </div>

            <button
              id="logout-button"
              class="border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Sign Out
            </button>

          </div>

        </div>

      </header>

      <div class="flex min-h-[calc(100vh-4rem)]">

        <aside class="hidden w-60 shrink-0 border-r border-slate-200 bg-white lg:block">

          <nav class="space-y-1 p-3">

            ${menu.map(
              (item) => `
                <button
                  class="nav-item text-slate-700 hover:bg-slate-100"
                  data-page="${item.page}"
                >
                  ${item.label}
                </button>
              `
            ).join('')}

          </nav>

        </aside>

        <main class="min-w-0 flex-1 p-5 md:p-7">

          <div class="mb-5 lg:hidden">

            <select
              id="mobile-navigation"
              class="field"
            >

              ${menu.map(
                (item) => `
                  <option value="${item.page}">
                    ${item.label}
                  </option>
                `
              ).join('')}

            </select>

          </div>

          <div id="portal-content"></div>

        </main>

      </div>

    </div>
  `

  document
    .querySelector('#logout-button')
    .addEventListener('click', () => {

      logout()

      window.location.href = '/'
    })

  document
    .querySelectorAll('[data-page]')
    .forEach((button) => {

      button.addEventListener('click', () => {

        navigate(
          button.dataset.page,
          role
        )

      })
    })

  document
    .querySelector('#mobile-navigation')
    .addEventListener('change', (event) => {

      navigate(
        event.target.value,
        role
      )

    })

  await renderDashboard(dashboard)
}

/*
 * ROLE BASED MENU
 */

function getMenuForRole(role) {

  if (role === 'OWNER') {

    return [
      {
        page: 'dashboard',
        label: 'Dashboard',
      },
      {
        page: 'instruments',
        label: 'My Instruments',
      },
      {
        page: 'applications',
        label: 'Applications',
      },
      {
        page: 'certificates',
        label: 'Certificates',
      },
      {
        page: 'search',
        label: 'Search',
      },
      {
        page: 'documents',
        label: 'Documents',
      },
    ]
  }

  if (
    role === 'LMO' ||
    role === 'ADMIN'
  ) {

    return [
      {
        page: 'dashboard',
        label: 'Dashboard',
      },
      {
        page: 'officer-applications',
        label: 'Verification Applications',
      },
      {
        page: 'certificates',
        label: 'Certificates',
      },
      {
        page: 'search',
        label: 'Search',
      },
      {
        page: 'documents',
        label: 'Documents',
      },
    ]
  }

  if (role === 'GATC') {

    return [
      {
        page: 'dashboard',
        label: 'Dashboard',
      },
      {
        page: 'inspections',
        label: 'Inspections',
      },
      {
        page: 'certificates',
        label: 'Certificates',
      },
      {
        page: 'search',
        label: 'Search',
      },
      {
        page: 'documents',
        label: 'Documents',
      },
    ]
  }

  return [
    {
      page: 'dashboard',
      label: 'Dashboard',
    },
  ]
}

/*
 * INTERNAL NAVIGATION
 */

async function navigate(page, role) {

  if (page === 'dashboard') {

    const dashboard =
      await apiFetch(
        '/verification/dashboard/'
      )

    await renderDashboard(dashboard)

    return
  }

  const content =
    document.querySelector(
      '#portal-content'
    )

  if (!content) return

  try {

    if (
      page === 'instruments' &&
      role === 'OWNER'
    ) {

      await renderPage(
        () => renderInstruments(),
        content
      )

      return
    }

    if (
      page === 'applications' &&
      role === 'OWNER'
    ) {

      await renderPage(
        () => renderApplications(),
        content
      )

      return
    }

    if (
      page === 'officer-applications' &&
      ['LMO', 'ADMIN'].includes(role)
    ) {

      await renderPage(
        () => renderOfficerApplications(),
        content
      )

      return
    }

    if (
      page === 'inspections' &&
      role === 'GATC'
    ) {

      await renderPage(
        () => renderInspections(),
        content
      )

      return
    }

    if (page === 'certificates') {

      await renderPage(
        () => renderCertificates(),
        content
      )

      return
    }

    if (page === 'search') {

      await renderPage(
        () => renderSearch(),
        content
      )

      return
    }

    if (page === 'documents') {

      await renderPage(
        () => renderDocuments(),
        content
      )

      return
    }

    content.innerHTML = `
      <div class="border border-slate-200 bg-white p-6">

        <div class="text-sm font-medium text-slate-900">
          Page unavailable
        </div>

        <div class="mt-1 text-sm text-slate-500">
          This section is not available for your account role.
        </div>

      </div>
    `

  } catch (error) {

    content.innerHTML = `
      <div class="border border-red-200 bg-white p-6">

        <div class="text-sm font-semibold text-red-700">
          Unable to load page
        </div>

        <div class="mt-1 text-sm text-slate-600">
          ${escapeHtml(error.message)}
        </div>

      </div>
    `
  }
}

async function renderPage(
  renderer,
  container
) {

  container.innerHTML = `
    <div class="border border-slate-200 bg-white p-6 text-sm text-slate-500">
      Loading...
    </div>
  `

  await renderer()
}

/*
 * DASHBOARD
 */

async function renderDashboard(data) {

  const content =
    document.querySelector(
      '#portal-content'
    )

  if (!content) return

  const stats =
    getDashboardStats(data)

  content.innerHTML = `
    <div>

      <div class="mb-7">

        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Dashboard
        </div>

        <h1 class="mt-1 text-2xl font-semibold text-slate-900">
          Overview
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Current status of Legal Metrology operations.
        </p>

      </div>

      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

        ${stats.map(
          (stat) => `
            <div class="border border-slate-200 bg-white p-5">

              <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                ${escapeHtml(stat.label)}
              </div>

              <div class="mt-3 text-3xl font-semibold text-slate-900">
                ${escapeHtml(stat.value)}
              </div>

            </div>
          `
        ).join('')}

      </div>

      <div class="mt-6 grid gap-6 xl:grid-cols-2">

        <div class="border border-slate-200 bg-white">

          <div class="border-b border-slate-200 px-5 py-4">

            <div class="text-sm font-semibold text-slate-900">
              Account
            </div>

          </div>

          <div class="divide-y divide-slate-100">

            ${infoRow(
              'Username',
              data.username
            )}

            ${infoRow(
              'Role',
              data.role
            )}

            ${infoRow(
              'System',
              'Legal Metrology Digital Portal'
            )}

          </div>

        </div>

        <div class="border border-slate-200 bg-white">

          <div class="border-b border-slate-200 px-5 py-4">

            <div class="text-sm font-semibold text-slate-900">
              Quick Actions
            </div>

          </div>

          <div class="grid gap-2 p-4 sm:grid-cols-2">

            ${getQuickActions(data.role)
              .map(
                (action) => `
                  <button
                    data-quick-page="${action.page}"
                    class="border border-slate-300 bg-white px-4 py-3 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    ${action.label}
                  </button>
                `
              )
              .join('')}

          </div>

        </div>

      </div>

    </div>
  `

  content
    .querySelectorAll(
      '[data-quick-page]'
    )
    .forEach((button) => {

      button.addEventListener(
        'click',
        async () => {

          const dashboard =
            await apiFetch(
              '/verification/dashboard/'
            )

          navigate(
            button.dataset.quickPage,
            dashboard.role
          )
        }
      )
    })
}

/*
 * DASHBOARD STATS
 */

function getDashboardStats(data) {

  if (data.role === 'OWNER') {

    return [
      {
        label: 'Registered Instruments',
        value:
          data.instrument_count ??
          data.instruments ??
          0,
      },
      {
        label: 'Applications',
        value:
          data.application_count ??
          data.applications ??
          0,
      },
      {
        label: 'Certificates',
        value:
          data.certificate_count ??
          data.certificates ??
          0,
      },
      {
        label: 'Active Certificates',
        value:
          data.active_certificate_count ??
          data.valid_certificates ??
          0,
      },
    ]
  }

  if (data.role === 'GATC') {

    return [
      {
        label: 'Assigned Applications',
        value:
          data.assigned_count ??
          data.assigned_applications ??
          0,
      },
      {
        label: 'Scheduled',
        value:
          data.scheduled_count ??
          data.scheduled_applications ??
          0,
      },
      {
        label: 'Inspections',
        value:
          data.inspection_count ??
          data.inspections ??
          0,
      },
      {
        label: 'Passed',
        value:
          data.passed_count ??
          data.passed_inspections ??
          0,
      },
    ]
  }

  return [
    {
      label: 'Applications',
      value:
        data.application_count ??
        data.applications ??
        0,
    },
    {
      label: 'Pending Review',
      value:
        data.pending_count ??
        data.pending_applications ??
        0,
    },
    {
      label: 'Scheduled',
      value:
        data.scheduled_count ??
        data.scheduled_applications ??
        0,
    },
    {
      label: 'Certificates',
      value:
        data.certificate_count ??
        data.certificates ??
        0,
    },
  ]
}

/*
 * QUICK ACTIONS
 */

function getQuickActions(role) {

  if (role === 'OWNER') {

    return [
      {
        page: 'instruments',
        label: 'Manage Instruments',
      },
      {
        page: 'applications',
        label: 'Verification Applications',
      },
      {
        page: 'certificates',
        label: 'View Certificates',
      },
      {
        page: 'documents',
        label: 'Documents',
      },
    ]
  }

  if (role === 'GATC') {

    return [
      {
        page: 'inspections',
        label: 'Open Inspections',
      },
      {
        page: 'certificates',
        label: 'View Certificates',
      },
      {
        page: 'search',
        label: 'Search Records',
      },
      {
        page: 'documents',
        label: 'Documents',
      },
    ]
  }

  return [
    {
      page: 'officer-applications',
      label: 'Verification Applications',
    },
    {
      page: 'certificates',
      label: 'View Certificates',
    },
    {
      page: 'search',
      label: 'Search Records',
    },
    {
      page: 'documents',
      label: 'Documents',
    },
  ]
}

function infoRow(label, value) {

  return `
    <div class="flex items-center justify-between gap-4 px-5 py-3">

      <div class="text-sm text-slate-500">
        ${escapeHtml(label)}
      </div>

      <div class="text-right text-sm font-medium text-slate-900">
        ${escapeHtml(value ?? '—')}
      </div>

    </div>
  `
}

function escapeHtml(value) {

  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}