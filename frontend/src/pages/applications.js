import { apiFetch } from '../api'

function formatStatus(status) {
  return String(status || '').replaceAll('_', ' ')
}

function statusBadge(status) {
  return `<span class="status-badge">${formatStatus(status)}</span>`
}

function formatDate(value) {
  if (!value) return '-'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleDateString('en-IN')
}

export async function renderApplications() {
  const app = document.querySelector('#app')

  app.innerHTML = `
    <div class="max-w-7xl mx-auto">

      <div class="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900">
            Verification Applications
          </h1>

          <p class="mt-1 text-sm text-slate-500">
            Submit and track verification, re-verification and renewal applications.
          </p>
        </div>

        <button
          id="new-application-button"
          class="bg-slate-900 px-4 py-3 text-sm font-medium text-white hover:bg-slate-800"
        >
          New Application
        </button>
      </div>

      <div id="applications-message" class="mb-4"></div>

      <div class="border border-slate-200 bg-white">

        <div class="border-b border-slate-200 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            My Applications
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="portal-table">
            <thead>
              <tr>
                <th>Application No.</th>
                <th>Instrument</th>
                <th>Type</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Previous Application</th>
              </tr>
            </thead>

            <tbody id="applications-body">
              <tr>
                <td colspan="6" class="text-center text-slate-500 py-8">
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

  document
    .querySelector('#new-application-button')
    .addEventListener('click', openNewApplicationModal)
}

async function loadApplications() {
  const body = document.querySelector('#applications-body')

  try {
    const data = await apiFetch('/verification/')

    const applications = Array.isArray(data)
      ? data
      : data.results || data.applications || []

    if (!applications.length) {
      body.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-slate-500 py-8">
            No applications found.
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
          ${formatStatus(application.application_type)}
        </td>

        <td>
          ${statusBadge(application.status)}
        </td>

        <td>
          ${formatDate(application.submitted_at)}
        </td>

        <td>
          ${
            application.previous_application_number ||
            application.previous_application?.application_number ||
            application.previous_application ||
            '-'
          }
        </td>

      </tr>
    `).join('')

  } catch (error) {

    body.innerHTML = `
      <tr>
        <td colspan="6" class="text-center text-red-600 py-8">
          ${error.message}
        </td>
      </tr>
    `
  }
}

async function openNewApplicationModal() {
  const modal = document.querySelector('#application-modal')

  modal.innerHTML = `
    <div class="fixed inset-0 z-50 bg-slate-900/40 flex items-center justify-center p-4">

      <div class="w-full max-w-xl border border-slate-200 bg-white">

        <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4">

          <div>
            <h2 class="text-lg font-semibold text-slate-900">
              New Verification Application
            </h2>

            <p class="mt-1 text-xs text-slate-500">
              Select an instrument and application type.
            </p>
          </div>

          <button
            id="close-application-modal"
            class="text-xl text-slate-400 hover:text-slate-900"
            type="button"
          >
            ×
          </button>

        </div>

        <form id="application-form" class="p-5">

          <div class="mb-5">

            <label class="label" for="application-instrument">
              Instrument
            </label>

            <select
              id="application-instrument"
              class="field"
              required
            >
              <option value="">
                Loading instruments...
              </option>
            </select>

          </div>

          <div class="mb-5">

            <label class="label" for="application-type">
              Application Type
            </label>

            <select
              id="application-type"
              class="field"
              required
            >
              <option value="INITIAL">
                Initial Verification
              </option>

              <option value="RE_VERIFICATION">
                Re-verification
              </option>

              <option value="RENEWAL">
                Renewal
              </option>
            </select>

          </div>

          <div
            id="previous-application-container"
            class="mb-5 hidden"
          >

            <label class="label" for="previous-application">
              Previous Application
            </label>

            <select
              id="previous-application"
              class="field"
            >
              <option value="">
                Select previous application
              </option>
            </select>

            <p class="mt-1 text-xs text-slate-500">
              Required for re-verification and renewal.
            </p>

          </div>

          <div class="mb-5">

            <label class="label" for="application-remarks">
              Remarks
            </label>

            <textarea
              id="application-remarks"
              class="field"
              rows="3"
              placeholder="Optional remarks"
            ></textarea>

          </div>

          <div id="application-form-message" class="mb-4"></div>

          <div class="flex justify-end gap-2">

            <button
              id="cancel-application"
              type="button"
              class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>

            <button
              id="submit-application"
              type="submit"
              class="bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Submit Application
            </button>

          </div>

        </form>

      </div>

    </div>
  `

  document
    .querySelector('#close-application-modal')
    .addEventListener('click', closeModal)

  document
    .querySelector('#cancel-application')
    .addEventListener('click', closeModal)

  document
    .querySelector('#application-form')
    .addEventListener('submit', submitApplication)

  document
    .querySelector('#application-type')
    .addEventListener('change', handleApplicationType)

  await loadInstruments()
}

function closeModal() {
  document.querySelector('#application-modal').innerHTML = ''
}

async function loadInstruments() {
  const select = document.querySelector('#application-instrument')

  try {
    const data = await apiFetch('/instruments/')

    const instruments = Array.isArray(data)
      ? data
      : data.results || data.instruments || []

    if (!instruments.length) {
      select.innerHTML = `
        <option value="">
          No instruments registered
        </option>
      `
      return
    }

    select.innerHTML = `
      <option value="">
        Select an instrument
      </option>

      ${instruments.map(instrument => `
        <option value="${instrument.id}">
          ${instrument.name} — ${instrument.serial_number}
        </option>
      `).join('')}
    `

  } catch (error) {

    select.innerHTML = `
      <option value="">
        Unable to load instruments
      </option>
    `

    showFormMessage(error.message, true)
  }
}

async function handleApplicationType() {
  const type = document.querySelector('#application-type').value
  const container = document.querySelector('#previous-application-container')
  const select = document.querySelector('#previous-application')

  if (type === 'INITIAL') {
    container.classList.add('hidden')
    select.required = false
    select.innerHTML = `
      <option value="">
        Not required
      </option>
    `
    return
  }

  container.classList.remove('hidden')
  select.required = true

  await loadPreviousApplications()
}

async function loadPreviousApplications() {
  const instrumentId =
    document.querySelector('#application-instrument').value

  const select = document.querySelector('#previous-application')

  if (!instrumentId) {
    select.innerHTML = `
      <option value="">
        Select an instrument first
      </option>
    `
    return
  }

  try {
    const data = await apiFetch('/verification/')

    const applications = Array.isArray(data)
      ? data
      : data.results || data.applications || []

    const previous = applications.filter(application => {
      const applicationInstrument =
        application.instrument_id ||
        application.instrument?.id ||
        application.instrument

      return String(applicationInstrument) === String(instrumentId)
    })

    if (!previous.length) {
      select.innerHTML = `
        <option value="">
          No previous applications found
        </option>
      `
      return
    }

    select.innerHTML = `
      <option value="">
        Select previous application
      </option>

      ${previous.map(application => `
        <option value="${application.id}">
          ${
            application.application_number ||
            `APP-${application.id}`
          }
          — ${formatStatus(application.status)}
        </option>
      `).join('')}
    `

  } catch (error) {

    select.innerHTML = `
      <option value="">
        Unable to load previous applications
      </option>
    `
  }
}

async function submitApplication(event) {
  event.preventDefault()

  const instrument = document.querySelector('#application-instrument').value
  const applicationType = document.querySelector('#application-type').value
  const previousApplication =
    document.querySelector('#previous-application').value

  const remarks =
    document.querySelector('#application-remarks').value.trim()

  if (!instrument) {
    showFormMessage('Please select an instrument.', true)
    return
  }

  if (
    applicationType !== 'INITIAL' &&
    !previousApplication
  ) {
    showFormMessage(
      'Please select the previous application.',
      true
    )
    return
  }

  const button = document.querySelector('#submit-application')

  button.disabled = true
  button.textContent = 'Submitting...'

  try {
    const payload = {
      instrument: Number(instrument),
      application_type: applicationType,
      remarks,
    }

    if (applicationType !== 'INITIAL') {
      payload.previous_application = Number(previousApplication)
    }

    const created = await apiFetch('/verification/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })

    showFormMessage(
      `Application ${
        created.application_number ||
        `APP-${created.id}`
      } submitted successfully.`,
      false
    )

    setTimeout(async () => {
      closeModal()
      await loadApplications()
    }, 900)

  } catch (error) {

    showFormMessage(error.message, true)

    button.disabled = false
    button.textContent = 'Submit Application'
  }
}

function showFormMessage(message, isError) {
  const element = document.querySelector('#application-form-message')

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
