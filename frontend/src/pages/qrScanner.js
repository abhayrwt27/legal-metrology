import { Html5Qrcode } from 'html5-qrcode'

let scanner = null

export function renderQrScanner() {
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
              Public QR Verification
            </div>
          </div>

          <button
            id="scanner-home"
            class="border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to Home
          </button>
        </div>
      </header>

      <main class="mx-auto max-w-2xl px-6 py-10">
        <div class="border border-slate-200 bg-white">
          <div class="border-b border-slate-200 px-6 py-5">
            <h1 class="text-xl font-semibold text-slate-900">
              Scan Instrument QR Code
            </h1>

            <p class="mt-1 text-sm text-slate-500">
              Allow camera access and point the camera at the permanent QR
              code attached to the instrument.
            </p>
          </div>

          <div class="p-6">
            <div
              id="qr-reader"
              class="min-h-[280px] border border-slate-300 bg-slate-50"
            ></div>

            <div
              id="scanner-status"
              class="mt-4 border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600"
            >
              Starting camera...
            </div>

            <div class="mt-5 border-t border-slate-200 pt-5">
              <div class="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Camera access
              </div>

              <p class="mt-1 text-sm leading-6 text-slate-600">
                Camera scanning normally requires HTTPS when the portal is
                deployed. On localhost, browsers generally allow camera
                access for development.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  `

  document.querySelector('#scanner-home').addEventListener('click', () => {
    stopScanner()
    window.location.href = '/'
  })

  startScanner()
}

async function startScanner() {
  const status = document.querySelector('#scanner-status')

  try {
    scanner = new Html5Qrcode('qr-reader')

    const cameras = await Html5Qrcode.getCameras()

    if (!cameras || cameras.length === 0) {
      throw new Error('No camera was found on this device.')
    }

    const preferredCamera =
      cameras.find((camera) =>
        /back|rear|environment/i.test(camera.label)
      ) || cameras[0]

    await scanner.start(
      preferredCamera.id,
      {
        fps: 10,
        qrbox: {
          width: 250,
          height: 250,
        },
        aspectRatio: 1,
      },
      (decodedText) => {
        handleQrResult(decodedText)
      },
      () => {
        // Ignore normal frame-by-frame scan failures.
      }
    )

    status.textContent = 'Camera ready. Point it at an instrument QR code.'
  } catch (error) {
    console.error(error)

    status.innerHTML = `
      <div class="font-medium text-red-700">
        Unable to start the camera.
      </div>

      <div class="mt-1">
        ${escapeHtml(error.message || 'Camera access was denied or unavailable.')}
      </div>

      <button
        id="retry-camera"
        class="mt-3 border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
      >
        Try Again
      </button>
    `

    document.querySelector('#retry-camera')?.addEventListener('click', () => {
      startScanner()
    })
  }
}

async function handleQrResult(decodedText) {
  if (!decodedText) return

  await stopScanner()

  const status = document.querySelector('#scanner-status')

  try {
    const url = new URL(decodedText, window.location.origin)

    if (url.pathname.startsWith('/verify/')) {
      window.location.href = url.href
      return
    }

    if (url.pathname.includes('/api/verification/public/instruments/')) {
      const parts = url.pathname.split('/').filter(Boolean)
      const uidIndex = parts.indexOf('instruments')

      if (uidIndex !== -1 && parts[uidIndex + 1]) {
        window.location.href = `/verify/${encodeURIComponent(parts[uidIndex + 1])}`
        return
      }
    }

    status.innerHTML = `
      <div class="font-medium text-red-700">
        Invalid QR code
      </div>
      <div class="mt-1 text-sm">
        This QR code is not a recognised Legal Metrology instrument QR code.
      </div>
    `
  } catch {
    status.innerHTML = `
      <div class="font-medium text-red-700">
        Invalid QR code
      </div>
      <div class="mt-1 text-sm">
        The scanned QR code does not contain a valid verification URL.
      </div>
    `
  }
}

async function stopScanner() {
  if (!scanner) return

  try {
    if (scanner.isScanning) {
      await scanner.stop()
    }

    scanner.clear()
  } catch (error) {
    console.warn('Unable to stop QR scanner:', error)
  }

  scanner = null
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}