export function renderHome() {
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
              Digital Verification Portal
            </div>
          </div>

          <button
            id="home-login"
            class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Officer / Owner Login
          </button>
        </div>
      </header>

      <main class="mx-auto max-w-7xl px-6 py-12">
        <section class="border border-slate-200 bg-white">
          <div class="grid gap-10 px-8 py-12 md:grid-cols-2 md:px-12">
            <div>
              <div class="mb-4 inline-block border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-blue-800">
                Public Verification Service
              </div>

              <h1 class="max-w-xl text-4xl font-bold tracking-tight text-slate-900">
                Verify a measuring instrument or certificate
              </h1>

              <p class="mt-5 max-w-xl text-base leading-7 text-slate-600">
                Scan the permanent QR code attached to a registered instrument
                or enter its instrument ID to view its current verification
                status and certificate history.
              </p>

              <div class="mt-8 flex flex-wrap gap-3">
                <button
                  id="home-scan"
                  class="bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
                >
                  Scan QR Code
                </button>

                <button
                  id="home-verify"
                  class="border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Verify Instrument ID
                </button>
              </div>
            </div>

            <div class="border border-slate-200 bg-slate-50 p-6">
              <h2 class="text-base font-semibold text-slate-900">
                Public verification
              </h2>

              <p class="mt-2 text-sm leading-6 text-slate-600">
                No account is required to verify publicly available
                instrument information.
              </p>

              <form id="instrument-form" class="mt-6">
                <label class="label">
                  Instrument UID
                </label>

                <input
                  id="instrument-uid"
                  class="field mt-2"
                  placeholder="Enter instrument UUID"
                  autocomplete="off"
                />

                <button
                  type="submit"
                  class="mt-3 w-full bg-blue-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
                >
                  Verify Instrument
                </button>
              </form>

              <div class="mt-6 border-t border-slate-200 pt-5">
                <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Permanent QR
                </div>

                <p class="mt-1 text-sm text-slate-600">
                  The QR code remains attached to the physical instrument
                  even when its verification certificate is renewed.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section class="mt-8 grid gap-4 md:grid-cols-3">
          <div class="border border-slate-200 bg-white p-5">
            <div class="text-sm font-semibold text-slate-900">
              Instrument Records
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Access the registered identity and basic details of an
              instrument.
            </p>
          </div>

          <div class="border border-slate-200 bg-white p-5">
            <div class="text-sm font-semibold text-slate-900">
              Verification History
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              View previous and current verification records associated with
              the instrument.
            </p>
          </div>

          <div class="border border-slate-200 bg-white p-5">
            <div class="text-sm font-semibold text-slate-900">
              Certificate Status
            </div>
            <p class="mt-2 text-sm leading-6 text-slate-600">
              Check whether the current certificate is valid, expired or
              revoked.
            </p>
          </div>
        </section>
      </main>

      <footer class="border-t border-slate-200 bg-white">
        <div class="mx-auto max-w-7xl px-6 py-5 text-xs text-slate-500">
          Legal Metrology Digital Portal
        </div>
      </footer>
    </div>
  `

  document.querySelector('#home-login').addEventListener('click', () => {
    window.location.href = '/login'
  })

  document.querySelector('#home-scan').addEventListener('click', () => {
    window.location.href = '/scan'
  })

  document.querySelector('#home-verify').addEventListener('click', () => {
    document.querySelector('#instrument-uid').focus()
  })

  document.querySelector('#instrument-form').addEventListener('submit', (event) => {
    event.preventDefault()

    const uid = document.querySelector('#instrument-uid').value.trim()

    if (!uid) {
      alert('Please enter an instrument UID.')
      return
    }

    window.location.href = `/verify/${encodeURIComponent(uid)}`
  })
}