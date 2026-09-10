import { apiFetch } from '../api'

export async function renderCertificates() {
  const container = document.getElementById('portal-content')

  container.innerHTML = `
    <div class="space-y-4">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Certificates</h1>
        <p class="mt-1 text-sm text-slate-500">
          View verification certificates issued for registered instruments.
        </p>
      </div>

      <div id="certificates-message" class="hidden"></div>

      <div class="border border-slate-200 bg-white">
        <div class="overflow-x-auto">
          <table class="portal-table">
            <thead>
              <tr>
                <th>Certificate No.</th>
                <th>Instrument</th>
                <th>Issue Date</th>
                <th>Valid Until</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody id="certificates-body">
              <tr>
                <td colspan="6" class="text-center text-slate-500">
                  Loading certificates...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `

  const body = document.getElementById('certificates-body')
  const message = document.getElementById('certificates-message')

  try {
    const data = await apiFetch('/verification/certificates/')

    const certificates = Array.isArray(data)
      ? data
      : data.results || data.certificates || []

    if (certificates.length === 0) {
      body.innerHTML = `
        <tr>
          <td colspan="6" class="py-8 text-center text-slate-500">
            No certificates found.
          </td>
        </tr>
      `
      return
    }

    body.innerHTML = certificates.map((certificate) => {
      const instrument =
        certificate.instrument_details ||
        certificate.instrument ||
        {}

      const status = certificate.status || 'UNKNOWN'

      return `
        <tr>
          <td>
            <div class="font-medium text-slate-900">
              ${escapeHtml(certificate.certificate_number || '-')}
            </div>
          </td>

          <td>
            <div class="font-medium text-slate-800">
              ${escapeHtml(instrument.name || '-')}
            </div>
            <div class="text-xs text-slate-500">
              ${escapeHtml(instrument.serial_number || '')}
            </div>
          </td>

          <td>
            ${escapeHtml(formatDate(certificate.issue_date))}
          </td>

          <td>
            ${escapeHtml(formatDate(certificate.valid_until))}
          </td>

          <td>
            <span class="status-badge">
              ${escapeHtml(status)}
            </span>
          </td>

          <td>
            <button
              class="text-sm font-medium text-blue-800 hover:text-blue-950"
              data-certificate="${escapeHtml(certificate.certificate_number || '')}"
            >
              View
            </button>
          </td>
        </tr>
      `
    }).join('')

    body.querySelectorAll('[data-certificate]').forEach((button) => {
      button.addEventListener('click', () => {
        const certificateNumber = button.dataset.certificate

        if (certificateNumber) {
          window.location.href =
            `/verify/certificate/${encodeURIComponent(certificateNumber)}`
        }
      })
    })
  } catch (error) {
    body.innerHTML = `
      <tr>
        <td colspan="6" class="py-8 text-center text-red-700">
          Unable to load certificates.
        </td>
      </tr>
    `

    message.className =
      'border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'

    message.textContent =
      error.message || 'Unable to load certificates.'
  }
}

function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}