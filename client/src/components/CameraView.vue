<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  camera: { type: Object, required: true },
})
const emit = defineEmits(['close'])

const dialog = ref(null)
const canvas = ref(null)
// Native resolution of the camera frames. The overlay uses it as its coordinate
// system, so regions of interest are drawn (and stored) relative to the frame.
const frameSize = ref(null)
const status = ref('Connecting to the camera…')
let socket = null

// The view takes the frame's aspect ratio (16:9 until the first frame arrives), as large
// as fits on screen. The canvas and the overlay both fill it exactly, so they line up.
const frameStyle = computed(() => {
  const { width, height } = frameSize.value ?? { width: 16, height: 9 }
  return {
    aspectRatio: `${width} / ${height}`,
    width: `min(100vw - 80px, ${(75 * width) / height}vh)`,
  }
})

onMounted(() => {
  dialog.value.showModal()

  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
  socket = new WebSocket(`${protocol}//${location.host}/api/cameras/${props.camera.id}/stream`)

  // Each message is one JPEG frame. Decoding is async, so a frame can finish after
  // a newer one; only draw frames newer than the one on screen.
  let received = 0
  let drawn = 0
  socket.onmessage = async ({ data }) => {
    const number = ++received
    const bitmap = await createImageBitmap(data)
    if (number > drawn) {
      drawn = number
      drawFrame(bitmap)
    }
    bitmap.close()
  }
  socket.onclose = ({ reason }) => {
    status.value = reason || 'Lost connection to the camera.'
  }
})

onBeforeUnmount(() => {
  socket.onmessage = null
  socket.onclose = null
  socket.close()
})

function drawFrame(bitmap) {
  const el = canvas.value
  if (!el) return
  if (el.width !== bitmap.width || el.height !== bitmap.height) {
    el.width = bitmap.width
    el.height = bitmap.height
    frameSize.value = { width: bitmap.width, height: bitmap.height }
  }
  el.getContext('2d').drawImage(bitmap, 0, 0)
  status.value = ''
}
</script>

<template>
  <dialog ref="dialog" class="camera-view" @close="emit('close')">
    <header>
      <h2>{{ camera.name }}</h2>
      <button type="button" @click="dialog.close()">Close</button>
    </header>

    <div class="frame" :style="frameStyle">
      <canvas ref="canvas" />
      <!-- Regions of interest go here, in frame pixel coordinates. -->
      <svg
        v-if="frameSize"
        class="overlay"
        :viewBox="`0 0 ${frameSize.width} ${frameSize.height}`"
      />
      <p v-if="status" class="status">{{ status }}</p>
    </div>
  </dialog>
</template>

<style scoped>
.camera-view {
  padding: 12px;
  border: none;
  border-radius: 8px;
}

.camera-view::backdrop {
  background: rgb(0 0 0 / 0.6);
}

header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.frame {
  position: relative;
  background: #000;
}

.frame canvas,
.overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.status {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  background: rgb(0 0 0 / 0.5);
  color: #fff;
}
</style>
