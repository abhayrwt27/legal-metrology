import { apiFetch } from '../api'

export async function renderInstruments() {
  const container = document.getElementById('portal-content')

  container.innerHTML = `
    <div class="space-y-4">
      <div class="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 class="text-xl font-semibold text-slate-900">
            My Instruments
          </h1>
          <p class="mt-1 text-sm text-slate-500">
            Register and manage weighing and measuring instruments.
          </p>
        </div>

        <button
          id="show-instrument-form"
          class="border border-slate-800 bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
        >
          Register Instrument
        </button>
      </div>

      <div id="instrument-message" class="hidden"></div>

      <div
        id="instrument-form-panel"
        class="hidden border border-slate-200 bg-white"
      >
        <div class="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Register Instrument
          </h2>
        </div>

        <form
          id="instrument-form"
          class="grid gap-4 p-4 md:grid-cols-2"
        >
          <div>
            <label class="label">Instrument Name</label>
            <input
              id="instrument-name"
              class="field"
              type="text"
              required
              placeholder="Example: Electronic Weighing Scale"
            />
          </div>

          <div>
            <label class="label">Instrument Type</label>
            <input
              id="instrument-type"
              class="field"
              type="text"
              required
              placeholder="Example: Weighing Instrument"
            />
          </div>

          <div>
            <label class="label">Manufacturer</label>
            <input
              id="instrument-manufacturer"
              class="field"
              type="text"
              placeholder="Manufacturer name"
            />
          </div>

          <div>
            <label class="label">Model Number</label>
            <input
              id="instrument-model"
              class="field"
              type="text"
              placeholder="Model number"
            />
          </div>

          <div>
            <label class="label">Serial Number</label>
            <input
              id="instrument-serial"
              class="field"
              type="text"
              required
              placeholder="Unique serial number"
            />
          </div>

          <div>
            <label class="label">Capacity</label>
            <input
              id="instrument-capacity"
              class="field"
              type="text"
              placeholder="Example: 100 kg"
            />
          </div>

          <div>
            <label class="label">Accuracy</label>
            <input
              id="instrument-accuracy"
              class="field"
              type="text"
              placeholder="Example: 10 g"
            />
          </div>

          <div>
            <label class="label">Purchase Date</label>
            <input
              id="instrument-purchase-date"
              class="field"
              type="date"
            />
          </div>

          <div class="md:col-span-2">
            <label class="label">Location</label>
            <input
              id="instrument-location"
              class="field"
              type="text"
              placeholder="Installation / business location"
            />
          </div>

          <div class="md:col-span-2">
            <label class="label">Description</label>
            <textarea
              id="instrument-description"
              class="field"
              rows="3"
              placeholder="Additional instrument information"
            ></textarea>
          </div>

          <div class="flex gap-2 md:col-span-2">
            <button
              type="submit"
              id="instrument-submit"
              class="border border-slate-800 bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              Register Instrument
            </button>

            <button
              type="button"
              id="cancel-instrument"
              class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>

      <div class="border border-slate-200 bg-white">
        <div class="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Registered Instruments
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="portal-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Serial Number</th>
                <th>Location</th>
                <th>Status</th>
                <th>Permanent ID</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody id="instruments-body">
              <tr>
                <td colspan="7" class="py-8 text-center text-slate-500">
                  Loading instruments...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `

  const formPanel = document.getElementById('instrument-form-panel')
  const showButton = document.getElementById('show-instrument-form')
  const cancelButton = document.getElementById('cancel-instrument')
  const form = document.getElementById('instrument-form')
  const submitButton = document.getElementById('instrument-submit')
  const body = document.getElementById('instruments-body')
  const message = document.getElementById('instrument-message')

  showButton.addEventListener('click', () => {
    formPanel.classList.remove('hidden')
    showButton.classList.add('hidden')
  })

  cancelButton.addEventListener('click', () => {
    form.reset()
    formPanel.classList.add('hidden')
    showButton.classList.remove('hidden')
  })

  form.addEventListener('submit', async (event) => {
    event.preventDefault()

    const payload = {
      name: value('instrument-name'),
      instrument_type: value('instrument-type'),
      manufacturer: value('instrument-manufacturer'),
      model_number: value('instrument-model'),
      serial_number: value('instrument-serial'),
      capacity: value('instrument-capacity'),
      accuracy: value('instrument-accuracy'),
      location: value('instrument-location'),
      purchase_date: value('instrument-purchase-date') || null,
      description: value('instrument-description'),
    }

    submitButton.disabled = true
    submitButton.textContent = 'Registering...'

    try {
      await apiFetch('/instruments/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })

      form.reset()
      formPanel.classList.add('hidden')
      showButton.classList.remove('hidden')

      showMessage(
        'Instrument registered successfully.',
        'success'
      )

      await loadInstruments()
    } catch (error) {
      showMessage(
        error.message || 'Unable to register instrument.',
        'error'
      )
    } finally {
      submitButton.disabled = false
      submitButton.textContent = 'Register Instrument'
    }
  })

  async function loadInstruments() {
    body.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500">
          Loading instruments...
        </td>
      </tr>
    `

    try {
      const data = await apiFetch('/instruments/')

      const instruments = Array.isArray(data)
        ? data
        : data.results || []

      if (instruments.length === 0) {
        body.innerHTML = `
          <tr>
            <td colspan="7" class="py-8 text-center text-slate-500">
              No instruments registered.
            </td>
          </tr>
        `
        return
      }

      body.innerHTML = instruments.map((instrument) => `
        <tr>
          <td>
            <div class="font-medium text-slate-900">
              ${escapeHtml(instrument.name || '-')}
            </div>
            <div class="text-xs text-slate-500">
              ${escapeHtml(instrument.manufacturer || '')}
            </div>
          </td>

          <td>
            ${escapeHtml(instrument.instrument_type || '-')}
          </td>

          <td>
            ${escapeHtml(instrument.serial_number || '-')}
          </td>

          <td>
            ${escapeHtml(instrument.location || '-')}
          </td>

          <td>
            <span class="status-badge">
              ${escapeHtml(instrument.status || '-')}
            </span>
          </td>

          <td>
            <div class="max-w-[180px] truncate font-mono text-xs text-slate-600">
              ${escapeHtml(instrument.instrument_uid || '-')}
            </div>
          </td>

          <td>
            <div class="flex flex-wrap gap-2">
              ${
                instrument.instrument_uid
                  ? `
                    <button
                      type="button"
                      data-verify="${escapeAttribute(instrument.instrument_uid)}"
                      class="text-sm font-medium text-blue-800 hover:text-blue-950"
                    >
                      Verify
                    </button>
                  `
                  : ''
              }

              ${
                instrument.id
                  ? `
                    <button
                      type="button"
                      data-delete="${escapeAttribute(instrument.id)}"
                      class="text-sm font-medium text-red-700 hover:text-red-900"
                    >
                      Delete
                    </button>
                  `
                  : ''
              }
            </div>
          </td>
        </tr>
      `).join('')

      body.querySelectorAll('[data-verify]').forEach((button) => {
        button.addEventListener('click', () => {
          window.location.href =
            `/verify/${encodeURIComponent(button.dataset.verify)}`
        })
      })

      body.querySelectorAll('[data-delete]').forEach((button) => {
        button.addEventListener('click', async () => {
          const id = button.dataset.delete

          if (!window.confirm(
            'Are you sure you want to delete this instrument?'
          )) {
            return
          }

          button.disabled = true

          try {
            await apiFetch(`/instruments/${id}/`, {
              method: 'DELETE',
            })

            showMessage(
              'Instrument deleted successfully.',
              'success'
            )

            await loadInstruments()
          } catch (error) {
            showMessage(
              error.message || 'Unable to delete instrument.',
              'error'
            )

            button.disabled = false
          }
        })
      })
    } catch (error) {
      body.innerHTML = `
        <tr>
          <td colspan="7" class="py-8 text-center text-red-700">
            Unable to load instruments.
          </td>
        </tr>
      `

      showMessage(
        error.message || 'Unable to load instruments.',
        'error'
      )
    }
  }

  function showMessage(text, type) {
    message.className =
      type === 'success'
        ? 'border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800'
        : 'border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'

    message.textContent = text
  }

  function value(id) {
    return document.getElementById(id).value.trim()
  }

  await loadInstruments()
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function escapeAttribute(value) {
  return escapeHtml(value)
}