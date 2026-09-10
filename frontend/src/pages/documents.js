import { apiFetch } from '../api'

export async function renderDocuments() {
  const container = document.getElementById('portal-content')

  container.innerHTML = `
    <div class="space-y-4">
      <div>
        <h1 class="text-xl font-semibold text-slate-900">Documents</h1>
        <p class="mt-1 text-sm text-slate-500">
          Upload and view documents associated with verification applications and instruments.
        </p>
      </div>

      <div id="document-message" class="hidden"></div>

      <div class="border border-slate-200 bg-white">
        <div class="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">Upload Document</h2>
        </div>

        <form id="document-form" class="grid gap-4 p-4 md:grid-cols-2">
          <div>
            <label class="label">Application ID</label>
            <input
              id="document-application"
              type="number"
              class="field"
              placeholder="Optional"
            />
          </div>

          <div>
            <label class="label">Instrument ID</label>
            <input
              id="document-instrument"
              type="number"
              class="field"
              placeholder="Optional"
            />
          </div>

          <div>
            <label class="label">Document Type</label>
            <select id="document-type" class="field">
              <option value="INSTRUMENT_PHOTO">Instrument Photo</option>
              <option value="VERIFICATION_DOCUMENT">
                Verification Document
              </option>
              <option value="INSPECTION_PHOTO">Inspection Photo</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div>
            <label class="label">File</label>
            <input
              id="document-file"
              type="file"
              class="field"
              required
            />
          </div>

          <div class="md:col-span-2">
            <label class="label">Description</label>
            <input
              id="document-description"
              type="text"
              class="field"
              placeholder="Document description"
            />
          </div>

          <div class="md:col-span-2">
            <button
              type="submit"
              id="document-submit"
              class="border border-slate-800 bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              Upload Document
            </button>
          </div>
        </form>
      </div>

      <div class="border border-slate-200 bg-white">
        <div class="border-b border-slate-200 bg-slate-50 px-4 py-3">
          <h2 class="text-sm font-semibold text-slate-900">
            Uploaded Documents
          </h2>
        </div>

        <div class="overflow-x-auto">
          <table class="portal-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Type</th>
                <th>Description</th>
                <th>Application</th>
                <th>Instrument</th>
                <th>Uploaded</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody id="documents-body">
              <tr>
                <td colspan="7" class="py-8 text-center text-slate-500">
                  Loading documents...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `

  const form = document.getElementById('document-form')
  const message = document.getElementById('document-message')
  const body = document.getElementById('documents-body')
  const submitButton = document.getElementById('document-submit')

  async function loadDocuments() {
    body.innerHTML = `
      <tr>
        <td colspan="7" class="py-8 text-center text-slate-500">
          Loading documents...
        </td>
      </tr>
    `

    try {
      const data = await apiFetch('/verification/documents/')

      const documents = Array.isArray(data)
        ? data
        : data.results || data.documents || []

      if (documents.length === 0) {
        body.innerHTML = `
          <tr>
            <td colspan="7" class="py-8 text-center text-slate-500">
              No documents uploaded.
            </td>
          </tr>
        `
        return
      }

      body.innerHTML = documents.map((document) => {
        const fileUrl = document.file || ''
        const fileName = getFileName(fileUrl)

        return `
          <tr>
            <td class="font-medium text-slate-900">
              ${escapeHtml(fileName)}
            </td>

            <td>
              ${escapeHtml(document.document_type || '-')}
            </td>

            <td>
              ${escapeHtml(document.description || '-')}
            </td>

            <td>
              ${escapeHtml(
                document.application ||
                document.application_id ||
                '-'
              )}
            </td>

            <td>
              ${escapeHtml(
                document.instrument ||
                document.instrument_id ||
                '-'
              )}
            </td>

            <td>
              ${escapeHtml(formatDate(document.uploaded_at))}
            </td>

            <td>
              ${
                fileUrl
                  ? `
                    <a
                      href="${escapeAttribute(fileUrl)}"
                      target="_blank"
                      rel="noopener noreferrer"
                      class="text-sm font-medium text-blue-800 hover:text-blue-950"
                    >
                      Open
                    </a>
                  `
                  : '-'
              }
            </td>
          </tr>
        `
      }).join('')
    } catch (error) {
      body.innerHTML = `
        <tr>
          <td colspan="7" class="py-8 text-center text-red-700">
            Unable to load documents.
          </td>
        </tr>
      `

      showMessage(
        error.message || 'Unable to load documents.',
        'error'
      )
    }
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault()

    const fileInput = document.getElementById('document-file')
    const file = fileInput.files[0]

    if (!file) {
      showMessage('Please select a file.', 'error')
      return
    }

    const application =
      document.getElementById('document-application').value.trim()

    const instrument =
      document.getElementById('document-instrument').value.trim()

    const documentType =
      document.getElementById('document-type').value

    const description =
      document.getElementById('document-description').value.trim()

    if (!application && !instrument) {
      showMessage(
        'Enter either an application ID or an instrument ID.',
        'error'
      )
      return
    }

    const formData = new FormData()

    if (application) {
      formData.append('application', application)
    }

    if (instrument) {
      formData.append('instrument', instrument)
    }

    formData.append('document_type', documentType)
    formData.append('file', file)
    formData.append('description', description)

    submitButton.disabled = true
    submitButton.textContent = 'Uploading...'

    try {
      await apiFetch('/verification/documents/', {
        method: 'POST',
        body: formData,
      })

      form.reset()

      showMessage(
        'Document uploaded successfully.',
        'success'
      )

      await loadDocuments()
    } catch (error) {
      showMessage(
        error.message || 'Document upload failed.',
        'error'
      )
    } finally {
      submitButton.disabled = false
      submitButton.textContent = 'Upload Document'
    }
  })

  function showMessage(text, type) {
    message.className =
      type === 'success'
        ? 'border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800'
        : 'border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700'

    message.textContent = text
  }

  await loadDocuments()
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

function getFileName(url) {
  if (!url) return '-'

  try {
    const pathname = new URL(url, window.location.origin).pathname
    return decodeURIComponent(pathname.split('/').pop() || 'Document')
  } catch {
    return url.split('/').pop() || 'Document'
  }
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