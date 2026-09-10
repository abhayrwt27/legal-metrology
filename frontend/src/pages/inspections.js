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

export async function renderInspections() {
  const app = document.querySelector('#app')

  app.innerHTML = `
    <div class="max-w-7xl mx-auto">

      <div class="mb-6">
        <h1 class="text-2xl font-semibold text-slate-900">
          Inspections
        </h1>

        <p class="mt-1 text-sm text-slate-500">
          Review applications assigned to this test centre and record inspection results.
        </p>
      </div>

      <div id="inspection-message" class="mb-4"></div>

      <div class="border border-slate-200 bg-white">

        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Assigned Applications
          </h2>

          <p class="mt-1 text-xs text-slate-500">
            Applications assigned by the Legal Metrology Officer.
          </p>
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
                <th>Submitted</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody id="assigned-applications-body">

              <tr>
                <td colspan="7" class="text-center text-slate-500 py-8">
                  Loading assigned applications...
                </td>
              </tr>

            </tbody>

          </table>

        </div>

      </div>

      <div id="inspection-modal"></div>

    </div>
  `

  await loadAssignedApplications()
}

async function loadAssignedApplications() {
  const body = document.querySelector('#assigned-applications-body')

  try {
    const data = await apiFetch('/verification/officer/applications/')

    const applications = Array.isArray(data)
      ? data
      : data.results || data.applications || []

    const assigned = applications.filter(application => {
      const status = application.status

      return (
        application.assigned_to ||
        application.assigned_to_username ||
        status === 'ASSIGNED' ||
        status === 'SCHEDULED' ||
        status === 'INSPECTION'
      )
    })

    if (!assigned.length) {

      body.innerHTML = `
        <tr>
          <td colspan="7" class="text-center py-10">

            <div class="text-sm font-medium text-slate-700">
              No applications assigned
            </div>

            <div class="mt-1 text-xs text-slate-500">
              Applications assigned to this test centre will appear here.
            </div>

          </td>
        </tr>
      `

      return
    }

    body.innerHTML = assigned.map(application => `
      <tr>

        <td>
          <div class="font-medium text-slate-900">
            ${
              application.application_number ||
              `APP-${application.id}`
            }
          </div>

          <div class="text-xs text-slate-500">
            ID: ${application.id}
          </div>
        </td>

        <td>
          ${
            application.instrument_name ||
            application.instrument?.name ||
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
          ${
            String(application.application_type || '-')
              .replaceAll('_', ' ')
          }
        </td>

        <td>
          ${statusBadge(application.status)}
        </td>

        <td>
          ${formatDate(application.submitted_at)}
        </td>

        <td>

          ${
            ['ASSIGNED', 'SCHEDULED', 'INSPECTION'].includes(
              application.status
            )
              ? `
                <button
                  class="inspection-action border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  data-id="${application.id}"
                >
                  Record Inspection
                </button>
              `
              : `
                <span class="text-xs text-slate-500">
                  ${formatDate(application.updated_at)}
                </span>
              `
          }

        </td>

      </tr>
    `).join('')

    document
      .querySelectorAll('.inspection-action')
      .forEach(button => {

        button.addEventListener('click', () => {

          const application = assigned.find(
            item => String(item.id) === button.dataset.id
          )

          if (application) {
            openInspectionModal(application)
          }

        })

      })

  } catch (error) {

    body.innerHTML = `
      <tr>
        <td colspan="7" class="text-center text-red-600 py-8">
          ${error.message}
        </td>
      </tr>
    `
  }
}

function openInspectionModal(application) {
  const modal = document.querySelector('#inspection-modal')

  modal.innerHTML = `
    <div class="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">

      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-slate-200 bg-white">

        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">

          <div>
            <h2 class="text-lg font-semibold text-slate-900">
              Record Inspection
            </h2>

            <p class="mt-1 text-sm text-slate-500">
              ${
                application.application_number ||
                `APP-${application.id}`
              }
            </p>
          </div>

          <button
            id="close-inspection-modal"
            type="button"
            class="text-xl text-slate-400 hover:text-slate-900"
          >
            ×
          </button>

        </div>

        <form id="inspection-form" class="p-5">

          <div class="mb-5 grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
              <div class="label">
                Application
              </div>

              <div class="text-sm font-medium text-slate-900">
                ${
                  application.application_number ||
                  `APP-${application.id}`
                }
              </div>
            </div>

            <div>
              <div class="label">
                Instrument
              </div>

              <div class="text-sm text-slate-900">
                ${
                  application.instrument_name ||
                  application.instrument?.name ||
                  '-'
                }
              </div>
            </div>

            <div>
              <div class="label">
                Application Status
              </div>

              <div>
                ${statusBadge(application.status)}
              </div>
            </div>

            <div>
              <div class="label">
                Applicant
              </div>

              <div class="text-sm text-slate-900">
                ${
                  application.applicant_username ||
                  application.applicant?.username ||
                  '-'
                }
              </div>
            </div>

          </div>

          <input
            id="inspection-application"
            type="hidden"
            value="${application.id}"
          />

          <div class="mb-5">

            <label class="label" for="inspection-date">
              Inspection Date
            </label>

            <input
              id="inspection-date"
              type="date"
              class="field"
              required
            />

          </div>

          <div class="mb-5">

            <label class="label" for="inspection-result">
              Inspection Result
            </label>

            <select
              id="inspection-result"
              class="field"
              required
            >

              <option value="">
                Select result
              </option>

              <option value="PASSED">
                Passed
              </option>

              <option value="FAILED">
                Failed
              </option>

            </select>

          </div>

          <div class="mb-5">

            <label class="label" for="inspection-measurements">
              Measurements
            </label>

            <textarea
              id="inspection-measurements"
              class="field"
              rows="5"
              placeholder='{"error": "0.02", "accuracy": "within permissible limit"}'
            ></textarea>

            <p class="mt-1 text-xs text-slate-500">
              Enter measurements as valid JSON.
            </p>

          </div>

          <div class="mb-5">

            <label class="label" for="inspection-remarks">
              Remarks
            </label>

            <textarea
              id="inspection-remarks"
              class="field"
              rows="3"
              placeholder="Inspection remarks"
            ></textarea>

          </div>

          <div id="inspection-form-message" class="mb-4"></div>

          <div class="flex justify-end gap-2">

            <button
              id="cancel-inspection"
              type="button"
              class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>

            <button
              id="submit-inspection"
              type="submit"
              class="bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Submit Inspection
            </button>

          </div>

        </form>

      </div>

    </div>
  `

  document
    .querySelector('#close-inspection-modal')
    .addEventListener('click', closeInspectionModal)

  document
    .querySelector('#cancel-inspection')
    .addEventListener('click', closeInspectionModal)

  document
    .querySelector('#inspection-form')
    .addEventListener('submit', submitInspection)

  document.querySelector('#inspection-date').value =
    new Date().toISOString().split('T')[0]
}

function closeInspectionModal() {
  document.querySelector('#inspection-modal').innerHTML = ''
}

async function submitInspection(event) {
  event.preventDefault()

  const application = Number(
    document.querySelector('#inspection-application').value
  )

  const inspectionDate =
    document.querySelector('#inspection-date').value

  const result =
    document.querySelector('#inspection-result').value

  const measurementsText =
    document.querySelector('#inspection-measurements').value.trim()

  const remarks =
    document.querySelector('#inspection-remarks').value.trim()

  if (!inspectionDate) {
    showInspectionMessage(
      'Please select the inspection date.',
      true
    )
    return
  }

  if (!result) {
    showInspectionMessage(
      'Please select the inspection result.',
      true
    )
    return
  }

  let measurements = {}

  if (measurementsText) {
    try {
      measurements = JSON.parse(measurementsText)
    } catch {
      showInspectionMessage(
        'Measurements must contain valid JSON.',
        true
      )
      return
    }
  }

  const button =
    document.querySelector('#submit-inspection')

  button.disabled = true
  button.textContent = 'Submitting...'

  try {

    await apiFetch('/verification/officer/inspections/', {
      method: 'POST',

      body: JSON.stringify({
        application,
        inspection_date: inspectionDate,
        measurements,
        result,
        remarks,
      }),
    })

    showInspectionMessage(
      'Inspection recorded successfully.',
      false
    )

    setTimeout(() => {
      closeInspectionModal()
      loadAssignedApplications()
    }, 900)

  } catch (error) {

    showInspectionMessage(
      error.message,
      true
    )

    button.disabled = false
    button.textContent = 'Submit Inspection'
  }
}

function showInspectionMessage(message, isError) {
  const element =
    document.querySelector('#inspection-form-message')

  if (!element) return

  element.innerHTML = `
    <div class="border ${
      isError
        ? 'border-red-200 bg-red-50 text-red-700'
        : 'border-green-200 bg-green-50 text-green-700'
    } px-3 py-2 text-sm">
      ${message}
    </div>
  `
}
