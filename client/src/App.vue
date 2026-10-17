<script setup>
import { onMounted, ref } from 'vue'
import { api } from './api'
import BarnMap from './components/BarnMap.vue'
import CameraForm from './components/CameraForm.vue'
import CameraView from './components/CameraView.vue'

const MAP_FILE_TYPES = 'image/png,image/jpeg,image/webp,image/gif'

const mapUrl = ref(null)
const cameras = ref([])
const loading = ref(true)
const error = ref('')
// The camera shown in the side panel: an existing one (has an id), or a new one
// that has been placed on the map but not saved yet (only x/y set).
const editing = ref(null)
// The camera whose live view is open.
const viewing = ref(null)

async function run(action) {
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(async () => {
  await run(async () => {
    const [map, cameraList] = await Promise.all([api.getMap(), api.listCameras()])
    mapUrl.value = map.image_url
    cameras.value = cameraList
  })
  loading.value = false
})

async function onMapFileChosen(event) {
  const file = event.target.files[0]
  event.target.value = ''
  if (!file) return
  await run(async () => {
    mapUrl.value = (await api.uploadMap(file)).image_url
  })
}

function placeCamera({ x, y }) {
  if (editing.value && !editing.value.id) {
    // Already placing a new camera: just move it, keeping what was typed in the form.
    editing.value = { ...editing.value, x, y }
  } else {
    editing.value = { name: '', stream_url: '', x, y }
  }
}

function selectCamera(camera) {
  editing.value = { ...camera }
}

async function moveCamera(camera, position) {
  const { id, name, stream_url } = camera
  const original = { x: camera.x, y: camera.y }
  // Show the new position right away; put it back if saving fails.
  setCameraPosition(id, position)
  await run(async () => {
    try {
      await api.updateCamera(id, { name, stream_url, ...position })
    } catch (e) {
      setCameraPosition(id, original)
      throw e
    }
  })
}

function setCameraPosition(id, position) {
  cameras.value = cameras.value.map((c) => (c.id === id ? { ...c, ...position } : c))
  // Keep an open edit form in sync, so saving it doesn't move the camera back.
  if (editing.value?.id === id) {
    editing.value = { ...editing.value, ...position }
  }
}

async function saveCamera(fields) {
  const { id, x, y } = editing.value
  const data = { ...fields, x, y }
  await run(async () => {
    if (id) {
      const updated = await api.updateCamera(id, data)
      cameras.value = cameras.value.map((c) => (c.id === id ? updated : c))
    } else {
      cameras.value.push(await api.createCamera(data))
    }
    editing.value = null
  })
}

// Host (and port) of a stream URL, without the scheme or credentials, for display.
function streamHost(url) {
  return url.replace(/^[a-z][a-z0-9+.-]*:\/\/([^/]*@)?/i, '').split('/')[0]
}

async function deleteCamera() {
  const { id, name } = editing.value
  if (!confirm(`Delete camera "${name}"?`)) return
  await run(async () => {
    await api.deleteCamera(id)
    cameras.value = cameras.value.filter((c) => c.id !== id)
    editing.value = null
  })
}
</script>

<template>
  <header class="app-header">
    <h1>Barn Management</h1>
    <label v-if="mapUrl" class="button">
      Replace map
      <input type="file" :accept="MAP_FILE_TYPES" hidden @change="onMapFileChosen" />
    </label>
  </header>

  <p v-if="error" class="error" role="alert">{{ error }}</p>

  <main v-if="loading" class="empty-state">Loading…</main>

  <main v-else-if="!mapUrl" class="empty-state">
    <p>Upload a map of your barns to start placing cameras.</p>
    <label class="button primary">
      Upload map
      <input type="file" :accept="MAP_FILE_TYPES" hidden @change="onMapFileChosen" />
    </label>
  </main>

  <main v-else class="workspace">
    <section class="map-area">
      <BarnMap
        :image-url="mapUrl"
        :cameras="cameras"
        :editing="editing"
        @place="placeCamera"
        @select="selectCamera"
        @move="moveCamera"
      />
    </section>

    <aside class="side-panel">
      <CameraForm
        v-if="editing"
        :key="editing.id ?? 'new'"
        :camera="editing"
        @save="saveCamera"
        @delete="deleteCamera"
        @cancel="editing = null"
        @view="viewing = editing"
      />
      <template v-else>
        <h2>Cameras</h2>
        <p class="hint">
          Click on the map where a camera is installed to register it. Drag a marker to move it.
        </p>
        <ul v-if="cameras.length" class="camera-list">
          <li v-for="camera in cameras" :key="camera.id">
            <button type="button" @click="selectCamera(camera)" class="camera-button">
              <strong>{{ camera.name }}</strong>
              <span style="width: 50%">{{ streamHost(camera.stream_url) }}</span>
            </button>
          </li>
        </ul>
        <p v-else class="hint">No cameras registered yet.</p>
      </template>
    </aside>
  </main>

  <CameraView v-if="viewing" :camera="viewing" @close="viewing = null" />
</template>
