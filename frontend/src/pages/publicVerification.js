import { API_BASE_URL } from '../api'

export async function renderPublicVerification(instrumentUid) {
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
              Public Verification Portal
            </div>
          </div>

          <div class="flex gap-2">
            <button
              id="verify-scan"
              class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Scan QR
            </button>

            <button
              id="verify-home"
              class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Home
            </button>
          </div>

        </div>
      </header>

      <main class="mx-auto max-w-5xl px-6 py-10">

        <div id="verification-content">
          <div class="border border-slate-200 bg-white p-8 text-sm text-slate-500">
            Loading instrument verification details...
          </div>
        </div>

      </main>

    </div>
  `

  document
    .querySelector('#verify-home')
    .addEventListener('click', () => {
      window.location.href = '/'
    })

  document
    .querySelector('#verify-scan')
    .addEventListener('click', () => {
      window.location.href = '/scan'
    })

  try {
    const response = await fetch(
      `${API_BASE_URL}/verification/public/instruments/${encodeURIComponent(instrumentUid)}/`
    )

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(
        data.detail ||
        data.error ||
        'Instrument verification record could not be found.'
      )
    }

    renderVerificationResult(data)
  } catch (error) {
    renderVerificationError(error)
  }
}

function renderVerificationResult(data) {
  const content =
    document.querySelector('#verification-content')

  /*
   * Backend response:
   *
   * {
   *   instrument: {...},
   *   current_certificate: {...},
   *   verification_history: [...]
   * }
   */

  const instrument =
    data.instrument || {}

  const certificate =
    data.current_certificate || null

  const history =
    data.verification_history || []

  const instrumentStatus =
    instrument.status || 'UNKNOWN'

  const certificateStatus =
    certificate?.status || 'NO CURRENT CERTIFICATE'

  content.innerHTML = `
    <div class="space-y-6">

      <!-- Instrument -->
      <section class="border border-slate-200 bg-white">

        <div class="flex flex-col justify-between gap-4 border-b border-slate-200 px-6 py-5 md:flex-row md:items-center">

          <div>

            <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Public Verification Result
            </div>

            <h1 class="mt-1 text-2xl font-semibold text-slate-900">
              ${escapeHtml(
                instrument.name ||
                'Registered Instrument'
              )}
            </h1>

            <p class="mt-1 text-sm text-slate-500">
              Instrument UID:
              <span class="font-mono text-slate-700">
                ${escapeHtml(
                  instrument.instrument_uid ||
                  '—'
                )}
              </span>
            </p>

          </div>

          <span class="${statusClass(instrumentStatus)}">
            ${escapeHtml(
              formatStatus(instrumentStatus)
            )}
          </span>

        </div>

        <div class="grid md:grid-cols-2">

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
            instrument.serial_number
          )}

          ${detailRow(
            'Capacity',
            instrument.capacity
          )}

          ${detailRow(
            'Accuracy',
            instrument.accuracy
          )}

          ${detailRow(
            'Location',
            instrument.location
          )}

          ${detailRow(
            'Purchase Date',
            instrument.purchase_date
          )}

        </div>

      </section>

      <!-- Current certificate -->
      <section class="border border-slate-200 bg-white">

        <div class="flex items-center justify-between border-b border-slate-200 px-6 py-5">

          <div>

            <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Current Certificate
            </div>

            <h2 class="mt-1 text-lg font-semibold text-slate-900">
              Verification Certificate
            </h2>

          </div>

          <span class="${statusClass(
            certificateStatus
          )}">
            ${escapeHtml(
              formatStatus(certificateStatus)
            )}
          </span>

        </div>

        ${
          certificate
            ? `
              <div class="grid md:grid-cols-2">

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
                  'Status',
                  formatStatus(certificate.status)
                )}

                ${detailRow(
                  'Issued By',
                  certificate.issued_by_username
                )}

              </div>

              <div class="border-t border-slate-200 px-6 py-4">

                <button
                  id="certificate-link"
                  class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Verify Certificate
                </button>

              </div>
            `
            : `
              <div class="px-6 py-8 text-sm text-slate-500">
                No current certificate is available for this instrument.
              </div>
            `
        }

      </section>

      <!-- History -->
      <section class="border border-slate-200 bg-white">

        <div class="border-b border-slate-200 px-6 py-5">

          <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Verification History
          </div>

          <h2 class="mt-1 text-lg font-semibold text-slate-900">
            Previous Verification Records
          </h2>

        </div>

        ${
          history.length
            ? `
              <div class="overflow-x-auto">

                <table class="w-full text-left text-sm">

                  <thead class="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">

                    <tr>
                      <th class="px-6 py-3 font-semibold">
                        Application
                      </th>

                      <th class="px-6 py-3 font-semibold">
                        Type
                      </th>

                      <th class="px-6 py-3 font-semibold">
                        Status
                      </th>

                      <th class="px-6 py-3 font-semibold">
                        Submitted
                      </th>

                      <th class="px-6 py-3 font-semibold">
                        Certificate
                      </th>
                    </tr>

                  </thead>

                  <tbody>
                    ${history
                      .map(historyRow)
                      .join('')}
                  </tbody>

                </table>

              </div>
            `
            : `
              <div class="px-6 py-8 text-sm text-slate-500">
                No verification history is available.
              </div>
            `
        }

      </section>

      <!-- Notice -->
      <section class="border border-slate-200 bg-slate-50 px-6 py-5">

        <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Verification Notice
        </div>

        <p class="mt-2 text-sm leading-6 text-slate-600">
          The QR code identifies the physical instrument, not an individual
          certificate. When the instrument is re-verified or renewed, the
          same QR code remains attached while the new certificate is added
          to its verification history.
        </p>

      </section>

    </div>
  `

  const certificateButton =
    document.querySelector(
      '#certificate-link'
    )

  if (certificateButton && certificate) {
    certificateButton.addEventListener(
      'click',
      () => {
        window.location.href =
          `/verify/certificate/${encodeURIComponent(
            certificate.certificate_number
          )}`
      }
    )
  }
}

function renderVerificationError(error) {
  const content =
    document.querySelector('#verification-content')

  content.innerHTML = `
    <div class="border border-red-200 bg-white p-8">

      <div class="text-sm font-semibold text-red-700">
        Verification record not found
      </div>

      <p class="mt-2 text-sm leading-6 text-slate-600">
        ${escapeHtml(
          error.message ||
          'Unable to retrieve the instrument record.'
        )}
      </p>

      <div class="mt-5 flex gap-2">

        <button
          id="try-again"
          class="bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
        >
          Return to Verification
        </button>

        <button
          id="error-scan"
          class="border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Scan QR
        </button>

      </div>

    </div>
  `

  document
    .querySelector('#try-again')
    .addEventListener('click', () => {
      window.location.href = '/'
    })

  document
    .querySelector('#error-scan')
    .addEventListener('click', () => {
      window.location.href = '/scan'
    })
}

function historyRow(item) {
  return `
    <tr class="border-b border-slate-100 last:border-b-0">

      <td class="px-6 py-4 font-medium text-slate-900">
        ${escapeHtml(
          item.application_number ||
          '—'
        )}
      </td>

      <td class="px-6 py-4 text-slate-600">
        ${escapeHtml(
          formatStatus(
            item.application_type
          )
        )}
      </td>

      <td class="px-6 py-4">

        <span class="${statusClass(
          item.status
        )}">
          ${escapeHtml(
            formatStatus(item.status)
          )}
        </span>

      </td>

      <td class="px-6 py-4 text-slate-600">
        ${escapeHtml(
          formatDate(
            item.submitted_at
          )
        )}
      </td>

      <td class="px-6 py-4 text-slate-600">
        ${
          item.certificate_number
            ? `
              <button
                class="certificate-history-link text-blue-700 hover:underline"
                data-certificate="${escapeHtml(
                  item.certificate_number
                )}"
              >
                ${escapeHtml(
                  item.certificate_number
                )}
              </button>
            `
            : '—'
        }
      </td>

    </tr>
  `
}

function detailRow(label, value) {
  return `
    <div class="border-b border-slate-100 px-6 py-4">

      <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
        ${escapeHtml(label)}
      </div>

      <div class="mt-1 text-sm font-medium text-slate-900">
        ${escapeHtml(
          value || '—'
        )}
      </div>

    </div>
  `
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return String(value)
  }

  return date.toLocaleDateString(
    'en-IN',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    }
  )
}

function formatStatus(value) {
  if (!value) return 'Unknown'

  return String(value)
    .replaceAll('_', ' ')
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    )
}

function statusClass(status) {
  const value =
    String(status || '')
      .toUpperCase()

  if (
    [
      'VERIFIED',
      'APPROVED',
      'VALID',
      'PASSED',
    ].includes(value)
  ) {
    return 'inline-flex border border-green-200 bg-green-50 px-2.5 py-1 text-xs font-semibold text-green-700'
  }

  if (
    [
      'REJECTED',
      'FAILED',
      'REVOKED',
      'EXPIRED',
    ].includes(value)
  ) {
    return 'inline-flex border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700'
  }

  if (
    [
      'UNDER_VERIFICATION',
      'UNDER_REVIEW',
      'ASSIGNED',
      'SCHEDULED',
      'INSPECTION',
    ].includes(value)
  ) {
    return 'inline-flex border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700'
  }

  return 'inline-flex border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-600'
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll(
      "'",
      '&#039;'
    )
}