import { API_BASE_URL } from '../api'

export async function renderPublicCertificate(certificateNumber) {
  const app = document.querySelector('#app')

  app.innerHTML = `
    <div class="min-h-screen bg-slate-100">
      <header class="border-b border-slate-200 bg-white">
        <div class="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <div class="text-lg font-semibold text-slate-900">
              Legal Metrology Department
            </div>
            <div class="text-xs text-slate-500">
              Public Certificate Verification
            </div>
          </div>

          <button
            id="certificate-home"
            class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Home
          </button>
        </div>
      </header>

      <main class="mx-auto max-w-4xl px-6 py-10">
        <div id="certificate-content">
          <div class="border border-slate-200 bg-white p-8 text-sm text-slate-500">
            Loading certificate...
          </div>
        </div>
      </main>
    </div>
  `

  document
    .querySelector('#certificate-home')
    .addEventListener('click', () => {
      window.location.href = '/'
    })

  try {
    const response = await fetch(
      `${API_BASE_URL}/verification/public/certificates/${encodeURIComponent(certificateNumber)}/`
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
        data.error ||
        'Certificate could not be found.'
      )
    }

    renderCertificate(data)
  } catch (error) {
    document.querySelector('#certificate-content').innerHTML = `
      <div class="border border-red-200 bg-white p-8">
        <div class="text-sm font-semibold text-red-700">
          Certificate not found
        </div>

        <p class="mt-2 text-sm leading-6 text-slate-600">
          ${escapeHtml(error.message)}
        </p>

        <button
          id="certificate-return"
          class="mt-5 bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Return to Home
        </button>
      </div>
    `

    document
      .querySelector('#certificate-return')
      .addEventListener('click', () => {
        window.location.href = '/'
      })
  }
}

function renderCertificate(data) {
  const content = document.querySelector('#certificate-content')

  const certificate = data.certificate || data
  const instrument = data.instrument || certificate.instrument_details || {}

  const status = certificate.status || 'UNKNOWN'

  content.innerHTML = `
    <div class="space-y-6">
      <section class="border border-slate-200 bg-white">
        <div class="flex flex-col justify-between gap-4 border-b border-slate-200 px-6 py-5 md:flex-row md:items-center">
          <div>
            <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Certificate Verification
            </div>

            <h1 class="mt-1 text-2xl font-semibold text-slate-900">
              ${escapeHtml(
                certificate.certificate_number || 'Certificate'
              )}
            </h1>
          </div>

          <span class="${statusClass(status)}">
            ${escapeHtml(formatStatus(status))}
          </span>
        </div>

        <div class="grid gap-0 md:grid-cols-2">
          ${detailRow(
            'Certificate Number',
            certificate.certificate_number
          )}

          ${detailRow(
            'Application Number',
            certificate.application_number
          )}

          ${detailRow(
            'Issue Date',
            certificate.issue_date
          )}

          ${detailRow(
            'Valid Until',
            certificate.valid_until
          )}

          ${detailRow(
            'Certificate Status',
            formatStatus(certificate.status)
          )}

          ${detailRow(
            'Issued By',
            certificate.issued_by_username
          )}
        </div>
      </section>

      <section class="border border-slate-200 bg-white">
        <div class="border-b border-slate-200 px-6 py-5">
          <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Instrument
          </div>

          <h2 class="mt-1 text-lg font-semibold text-slate-900">
            Registered Instrument
          </h2>
        </div>

        <div class="grid gap-0 md:grid-cols-2">
          ${detailRow(
            'Instrument Name',
            certificate.instrument_name || instrument.name
          )}

          ${detailRow(
            'Instrument Type',
            instrument.instrument_type
          )}

          ${detailRow(
            'Manufacturer',
            instrument.manufacturer
          )}

          ${detailRow(
            'Model Number',
            instrument.model_number
          )}

          ${detailRow(
            'Serial Number',
            certificate.instrument_serial_number ||
            instrument.serial_number
          )}

          ${detailRow(
            'Instrument UID',
            certificate.instrument_uid ||
            instrument.instrument_uid
          )}
        </div>
      </section>

      <section class="border border-slate-200 bg-slate-50 px-6 py-5">
        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Public Record
        </div>

        <p class="mt-2 text-sm leading-6 text-slate-600">
          This information is provided for public verification of a Legal
          Metrology certificate. Certificate status should be checked against
          the latest record available in the portal.
        </p>
      </section>
    </div>
  `
}

function detailRow(label, value) {
  return `
    <div class="border-b border-slate-100 px-6 py-4">
      <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
        ${escapeHtml(label)}
      </div>

      <div class="mt-1 text-sm font-medium text-slate-900">
        ${escapeHtml(value || '—')}
      </div>
    </div>
  `
}

function formatStatus(value) {
  if (!value) return 'Unknown'

  return String(value)
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function statusClass(status) {
  const value = String(status || '').toUpperCase()

  if (value === 'VALID') {
    return 'inline-flex border border-green-200 bg-green-50 px-2.5 py-1 text-xs font-semibold text-green-700'
  }

  if (['EXPIRED', 'REVOKED'].includes(value)) {
    return 'inline-flex border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700'
  }

  return 'inline-flex border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600'
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}