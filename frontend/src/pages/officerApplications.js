import { apiFetch } from '../api'

function statusBadge(status) {
  return `<span class="status-badge">${String(status || '').replaceAll('_', ' ')}</span>`
}

function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString('en-IN')
}

export async function renderOfficerApplications() {
  const app = document.querySelector('#app')

  app.innerHTML = `
    <div class="max-w-7xl mx-auto">

      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-slate-900">
          Verification Applications
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Review and process submitted verification applications.
        </p>
      </div>

      <div class="border border-slate-200 bg-white">

        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Applications
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="portal-table">

            <thead>
              <tr>
                <th>Application</th>
                <th>Instrument</th>
                <th>Applicant</th>
                <th>Type</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Submitted</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody id="applications-body">

              <tr>
                <td colspan="8" class="text-center text-slate-500 py-8">
                  Loading applications...
                </td>
              </tr>

            </tbody>

          </table>
        </div>

      </div>

      <div id="application-modal"></div>

    </div>
  `

  await loadApplications()
}

async function loadApplications() {
  const body = document.querySelector('#applications-body')

  try {
    const data = await apiFetch('/verification/officer/applications/')

    const applications = Array.isArray(data)
      ? data
      : data.results || data.applications || []

    if (!applications.length) {
      body.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-slate-500 py-8">
            No verification applications found.
          </td>
        </tr>
      `
      return
    }

    body.innerHTML = applications.map(application => `
      <tr>

        <td>
          <div class="font-medium text-slate-900">
            ${application.application_number || `APP-${application.id}`}
          </div>

          <div class="text-xs text-slate-500">
            ID: ${application.id}
          </div>
        </td>

        <td>
          ${
            application.instrument_name ||
            application.instrument?.name ||
            application.instrument ||
            '-'
          }
        </td>

        <td>
          ${
            application.applicant_username ||
            application.applicant?.username ||
            '-'
          }
        </td>

        <td>
          ${String(application.application_type || '-').replaceAll('_', ' ')}
        </td>

        <td>
          ${statusBadge(application.status)}
        </td>

        <td>
          ${
            application.assigned_to_username ||
            application.assigned_to?.username ||
            'Not assigned'
          }
        </td>

        <td>
          ${formatDate(application.submitted_at)}
        </td>

        <td>
          <button
            class="application-action border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
            data-id="${application.id}"
          >
            Manage
          </button>
        </td>

      </tr>
    `).join('')

    document.querySelectorAll('.application-action').forEach(button => {

      button.addEventListener('click', () => {

        const application = applications.find(
          item => String(item.id) === button.dataset.id
        )

        if (application) {
          openApplicationModal(application)
        }

      })

    })

  } catch (error) {

    body.innerHTML = `
      <tr>
        <td colspan="8" class="text-center text-red-600 py-8">
          ${error.message}
        </td>
      </tr>
    `
  }
}

async function openApplicationModal(application) {
  const modal = document.querySelector('#application-modal')

  const canDecide =
    application.status === 'INSPECTION'

  modal.innerHTML = `
    <div class="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">

      <div class="w-full max-w-2xl border border-slate-200 bg-white max-h-[90vh] overflow-y-auto">

        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">

          <div>
            <h2 class="text-lg font-semibold text-slate-900">
              Manage Application
            </h2>

            <p class="mt-1 text-sm text-slate-500">
              ${application.application_number || `APP-${application.id}`}
            </p>
          </div>

          <button
            id="close-application-modal"
            type="button"
            class="text-xl text-slate-400 hover:text-slate-900"
          >
            ×
          </button>

        </div>

        <div class="p-5 space-y-5">

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
              <div class="label">Instrument</div>
              <div class="text-sm text-slate-900">
                ${
                  application.instrument_name ||
                  application.instrument?.name ||
                  '-'
                }
              </div>
            </div>

            <div>
              <div class="label">Application Type</div>
              <div class="text-sm text-slate-900">
                ${
                  String(application.application_type || '-')
                    .replaceAll('_', ' ')
                }
              </div>
            </div>

            <div>
              <div class="label">Applicant</div>
              <div class="text-sm text-slate-900">
                ${
                  application.applicant_username ||
                  application.applicant?.username ||
                  '-'
                }
              </div>
            </div>

            <div>
              <div class="label">Current Status</div>
              <div>
                ${statusBadge(application.status)}
              </div>
            </div>

          </div>

          <div class="border-t border-slate-200 pt-5">

            <h3 class="text-sm font-semibold text-slate-900 mb-3">
              Test Centre Assignment
            </h3>

            ${
              application.status === 'SUBMITTED'
              ? `
                <div class="flex gap-2">

                  <select id="gatc-select" class="field flex-1">
                    <option value="">
                      Loading test centres...
                    </option>
                  </select>

                  <button
                    id="assign-button"
                    type="button"
                    class="bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                  >
                    Assign
                  </button>

                </div>
              `
              : `
                <div class="border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-600">
                  ${
                    application.assigned_to_username ||
                    application.assigned_to?.username
                      ? `Assigned to ${application.assigned_to_username || application.assigned_to.username}.`
                      : 'Assignment is not available at the current stage.'
                  }
                </div>
              `
            }

          </div>

          ${
            canDecide
            ? `
              <div class="border-t border-slate-200 pt-5">

                <h3 class="text-sm font-semibold text-slate-900 mb-3">
                  Application Decision
                </h3>

                <p class="mb-4 text-sm text-slate-500">
                  Inspection has been completed. You can now approve or reject this application.
                </p>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">

                  <select id="decision-select" class="field">
                    <option value="">
                      Select decision
                    </option>

                    <option value="APPROVED">
                      Approve
                    </option>

                    <option value="REJECTED">
                      Reject
                    </option>
                  </select>

                  <input
                    id="decision-remarks"
                    class="field"
                    placeholder="Remarks"
                  />

                </div>

                <button
                  id="decision-button"
                  type="button"
                  class="mt-3 w-full bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                >
                  Submit Decision
                </button>

              </div>
            `
            : `
              <div class="border-t border-slate-200 pt-5">

                <h3 class="text-sm font-semibold text-slate-900 mb-2">
                  Next Step
                </h3>

                <p class="text-sm text-slate-500">
                  ${
                    application.status === 'SUBMITTED'
                      ? 'Assign this application to a Government Approved Test Centre for inspection.'
                      : application.status === 'ASSIGNED'
                        ? 'The assigned Test Centre must complete the inspection before a decision can be made.'
                        : application.status === 'SCHEDULED'
                          ? 'The scheduled inspection must be completed before a decision can be made.'
                          : 'No decision is required at the current stage.'
                  }
                </p>

              </div>
            `
          }

          <div id="modal-message"></div>

        </div>

      </div>

    </div>
  `

  document
    .querySelector('#close-application-modal')
    .addEventListener('click', closeModal)

  if (application.status === 'SUBMITTED') {
    await loadGATCs()

    document
      .querySelector('#assign-button')
      .addEventListener('click', () => assignApplication(application))
  }

  if (canDecide) {
    document
      .querySelector('#decision-button')
      .addEventListener('click', () => submitDecision(application))
  }
}

function closeModal() {
  document.querySelector('#application-modal').innerHTML = ''
}

async function loadGATCs() {
  const select = document.querySelector('#gatc-select')

  if (!select) return

  try {
    const data = await apiFetch('/auth/gatcs/')

    const gatcs = Array.isArray(data)
      ? data
      : data.results || data.gatcs || []

    if (!gatcs.length) {
      select.innerHTML = `
        <option value="">
          No test centres available
        </option>
      `
      return
    }

    select.innerHTML = `
      <option value="">
        Select test centre
      </option>

      ${gatcs.map(gatc => `
        <option value="${gatc.id}">
          ${gatc.username}${gatc.email ? ` — ${gatc.email}` : ''}
        </option>
      `).join('')}
    `

  } catch (error) {

    select.innerHTML = `
      <option value="">
        Unable to load test centres
      </option>
    `
  }
}

async function assignApplication(application) {
  const select = document.querySelector('#gatc-select')
  const modalMessage = document.querySelector('#modal-message')
  const button = document.querySelector('#assign-button')

  if (!select?.value) {
    modalMessage.innerHTML = `
      <p class="text-sm text-red-600">
        Please select a test centre.
      </p>
    `
    return
  }

  button.disabled = true
  button.textContent = 'Assigning...'

  try {

    await apiFetch(
      `/verification/officer/applications/${application.id}/assign/`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          officer_id: Number(select.value),
        }),
      }
    )

    modalMessage.innerHTML = `
      <div class="border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
        Application assigned successfully.
      </div>
    `

    setTimeout(() => {
      closeModal()
      loadApplications()
    }, 900)

  } catch (error) {

    modalMessage.innerHTML = `
      <p class="text-sm text-red-600">
        ${error.message}
      </p>
    `

    button.disabled = false
    button.textContent = 'Assign'
  }
}

async function submitDecision(application) {
  const decision = document.querySelector('#decision-select')?.value
  const remarks =
    document.querySelector('#decision-remarks')?.value || ''

  const modalMessage = document.querySelector('#modal-message')
  const button = document.querySelector('#decision-button')

  if (!decision) {
    modalMessage.innerHTML = `
      <p class="text-sm text-red-600">
        Please select a decision.
      </p>
    `
    return
  }

  button.disabled = true
  button.textContent = 'Submitting...'

  try {

    await apiFetch(
      `/verification/officer/applications/${application.id}/decision/`,
      {
        method: 'PATCH',
        body: JSON.stringify({
          status: decision,
          remarks,
        }),
      }
    )

    modalMessage.innerHTML = `
      <div class="border border-green-200 bg-green-50 px-3 py-2 text-sm text-green-700">
        Decision submitted successfully.
      </div>
    `

    setTimeout(() => {
      closeModal()
      loadApplications()
    }, 900)

  } catch (error) {

    modalMessage.innerHTML = `
      <p class="text-sm text-red-600">
        ${error.message}
      </p>
    `

    button.disabled = false
    button.textContent = 'Submit Decision'
  }
}
