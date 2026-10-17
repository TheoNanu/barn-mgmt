async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, options)
  if (!response.ok) {
    throw new Error(await errorMessage(response))
  }
  return response.status === 204 ? null : response.json()
}

async function errorMessage(response) {
  try {
    const { detail } = await response.json()
    // FastAPI validation errors come as a list of { loc, msg } objects.
    if (Array.isArray(detail)) {
      return detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join(', ')
    }
    return detail ?? response.statusText
  } catch {
    return response.statusText
  }
}

function json(method, body) {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

export const api = {
  getMap: () => request('/map'),
  uploadMap(file) {
    const body = new FormData()
    body.append('file', file)
    return request('/map', { method: 'PUT', body })
  },
  listCameras: () => request('/cameras'),
  createCamera: (camera) => request('/cameras', json('POST', camera)),
  updateCamera: (id, camera) => request(`/cameras/${id}`, json('PUT', camera)),
  deleteCamera: (id) => request(`/cameras/${id}`, { method: 'DELETE' }),
}
