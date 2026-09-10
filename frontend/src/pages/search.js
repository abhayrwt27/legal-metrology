import { apiFetch } from '../api'

export async function renderSearch() {
  const container = document.getElementById('portal-content')

  container.innerHTML = `
    <div class="space-y-4">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Search Records</h1>
        <p class="mt-1 text-sm text-slate-500">
          Search instruments, applications and certificates across the portal.
        </p>
      </div>

      <div class="border border-slate-200 bg-white">
        <form id="search-form" class="flex flex-col gap-3 p-4 sm:flex-row">
          <input
            id="search-input"
            type="search"
            class="field flex-1"
            placeholder="Search by certificate number, serial number, application number or instrument name"
            autocomplete="off"
          />

          <button
            id="search-button"
            type="submit"
            class="border border-slate-800 bg-slate-800 px-5 py-2 text-sm font-medium text-white hover:bg-slate-700"
          >
            Search
          </button>
        </form>
      </div>

      <div id="search-message" class="hidden"></div>

      <div class="border border-slate-200 bg-white">
        <div class="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Search Results
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="portal-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Reference</th>
                <th>Name / Instrument</th>
                <th>Status</th>
                <th>Details</th>
              </tr>
            </thead>

            <tbody id="search-body">
              <tr>
                <td colspan="5" class="py-8 text-center text-slate-500">
                  Enter a search term to find records.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `

  const form = document.getElementById('search-form')
  const input = document.getElementById('search-input')
  const button = document.getElementById('search-button')
  const body = document.getElementById('search-body')
  const message = document.getElementById('search-message')

  form.addEventListener('submit', async (event) => {
    event.preventDefault()

    const query = input.value.trim()

    if (!query) {
      showMessage('Enter a search term.', 'error')
      return
    }

    button.disabled = true
    button.textContent = 'Searching...'

    body.innerHTML = `
      <tr>
        <td colspan="5" class="py-8 text-center text-slate-500">
          Searching records...
        </td>
      </tr>
    `

    message.className = 'hidden'

    try {
      const data = await apiFetch(
        `/verification/search/?q=${encodeURIComponent(query)}`
      )

      renderResults(data)
    } catch (error) {
      body.innerHTML = `
        <tr>
          <td colspan="5" class="py-8 text-center text-red-700">
            Unable to complete the search.
          </td>
        </tr>
      `

      showMessage(
        error.message || 'Search failed.',
        'error'
      )
    } finally {
      button.disabled = false
      button.textContent = 'Search'
    }
  })

  function renderResults(data) {
    const results = normalizeResults(data)

    if (results.length === 0) {
      body.innerHTML = `
        <tr>
          <td colspan="5" class="py-8 text-center text-slate-500">
            No matching records found.
          </td>
        </tr>
      `
      return
    }

    body.innerHTML = results.map((item) => {
      const type =
        item.type ||
        item.record_type ||
        item.model ||
        'Record'

      const reference =
        item.reference ||
        item.application_number ||
        item.certificate_number ||
        item.serial_number ||
        item.id ||
        '-'

      const name =
        item.name ||
        item.instrument_name ||
        item.instrument?.name ||
        item.instrument_details?.name ||
        '-'

      const status =
        item.status ||
        item.instrument?.status ||
        '-'

      return `
        <tr>
          <td>
            <span class="font-medium text-slate-700">
              ${escapeHtml(formatType(type))}
            </span>
          </td>

          <td>
            <span class="font-medium text-slate-900">
              ${escapeHtml(reference)}
            </span>
          </td>

          <td>
            ${escapeHtml(name)}
          </td>

          <td>
            <span class="status-badge">
              ${escapeHtml(status)}
            </span>
          </td>

          <td>
            ${renderAction(item, type)}
          </td>
        </tr>
      `
    }).join('')

    body.querySelectorAll('[data-search-action]').forEach((button) => {
      button.addEventListener('click', () => {
        const url = button.dataset.searchAction

        if (url) {
          window.location.href = url
        }
      })
    })
  }

  function renderAction(item, type) {
    if (
      type.toLowerCase().includes('certificate') &&
      item.certificate_number
    ) {
      return `
        <button
          type="button"
          data-search-action="/verify/certificate/${encodeURIComponent(item.certificate_number)}"
          class="text-sm font-medium text-blue-800 hover:text-blue-950"
        >
          View
        </button>
      `
    }

    if (
      item.instrument_uid ||
      item.instrument?.instrument_uid
    ) {
      const uid =
        item.instrument_uid ||
        item.instrument.instrument_uid

      return `
        <button
          type="button"
          data-search-action="/verify/${encodeURIComponent(uid)}"
          class="text-sm font-medium text-blue-800 hover:text-blue-950"
        >
          Verify
        </button>
      `
    }

    return '-'
  }

  function normalizeResults(data) {
    if (Array.isArray(data)) {
      return data
    }

    if (Array.isArray(data.results)) {
      return data.results
    }

    const combined = []

    if (Array.isArray(data.instruments)) {
      combined.push(
        ...data.instruments.map((item) => ({
          ...item,
          type: 'Instrument',
        }))
      )
    }

    if (Array.isArray(data.applications)) {
      combined.push(
        ...data.applications.map((item) => ({
          ...item,
          type: 'Application',
        }))
      )
    }

    if (Array.isArray(data.certificates)) {
      combined.push(
        ...data.certificates.map((item) => ({
          ...item,
          type: 'Certificate',
        }))
      )
    }

    return combined
  }

  function showMessage(text, type) {
    message.className =
      type === 'success'
        ? 'border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800'
        : 'border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'

    message.textContent = text
  }
}

function formatType(value) {
  return String(value)
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}