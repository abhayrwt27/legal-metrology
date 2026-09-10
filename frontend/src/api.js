const API_BASE_URL = '/api'

async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      username,
      password,
    }),
  })

  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.detail ||
      data.non_field_errors?.[0] ||
      'Invalid username or password.'
    )
  }

  localStorage.setItem('access_token', data.access)
  localStorage.setItem('refresh_token', data.refresh)

  return data
}

function getAccessToken() {
  return localStorage.getItem('access_token')
}

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

async function apiFetch(endpoint, options = {}) {
  const token = getAccessToken()

  const headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  }

  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (response.status === 401) {
    logout()
    window.location.reload()
    throw new Error('Session expired. Please sign in again.')
  }

  const contentType = response.headers.get('content-type') || ''

  if (contentType.includes('application/json')) {
    const data = await response.json()

    if (!response.ok) {
      throw new Error(
        data.detail ||
        data.non_field_errors?.[0] ||
        'Request failed.'
      )
    }

    return data
  }

  if (!response.ok) {
    throw new Error('Request failed.')
  }

  return response
}

export {
  API_BASE_URL,
  login,
  getAccessToken,
  logout,
  apiFetch,
}