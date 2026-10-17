<script setup>
import { ref } from 'vue'

defineProps({
  imageUrl: { type: String, required: true },
  cameras: { type: Array, required: true },
  // The camera currently being edited or placed, if any.
  editing: { type: Object, default: null },
})
const emit = defineEmits(['place', 'select', 'move'])

// How far the pointer must travel before a press on a marker counts as a drag.
const DRAG_THRESHOLD_PX = 4

const image = ref(null)
// The marker being dragged: { id, startX, startY, moved, x, y }.
const drag = ref(null)
// A drag ends with a click on the marker, which must not also select it.
let justDragged = false

const clamp = (value) => Math.min(1, Math.max(0, value))

// Positions are stored as fractions of the image size, independent of display size.
function toMapPosition(event) {
  const rect = image.value.getBoundingClientRect()
  return {
    x: clamp((event.clientX - rect.left) / rect.width),
    y: clamp((event.clientY - rect.top) / rect.height),
  }
}

function onImageClick(event) {
  emit('place', toMapPosition(event))
}

function onMarkerPointerDown(event, camera) {
  if (event.button !== 0) return
  justDragged = false
  event.currentTarget.setPointerCapture(event.pointerId)
  drag.value = { id: camera.id, startX: event.clientX, startY: event.clientY, moved: false }
}

function onMarkerPointerMove(event) {
  const d = drag.value
  if (!d) return
  if (!d.moved && Math.hypot(event.clientX - d.startX, event.clientY - d.startY) < DRAG_THRESHOLD_PX) {
    return
  }
  Object.assign(d, { moved: true }, toMapPosition(event))
}

function onMarkerPointerUp(camera) {
  const d = drag.value
  drag.value = null
  if (d?.moved) {
    justDragged = true
    emit('move', camera, { x: d.x, y: d.y })
  }
}

function onMarkerClick(camera) {
  if (justDragged) {
    justDragged = false
    return
  }
  emit('select', camera)
}

function isDragging(camera) {
  return drag.value?.id === camera.id && drag.value.moved
}

function position({ x, y }) {
  return { left: `${x * 100}%`, top: `${y * 100}%` }
}
</script>

<template>
  <div class="barn-map">
    <img ref="image" :src="imageUrl" alt="Barn map" draggable="false" @click="onImageClick" />

    <button
      v-for="camera in cameras"
      :key="camera.id"
      type="button"
      class="marker"
      :class="{ selected: editing?.id === camera.id, dragging: isDragging(camera) }"
      :style="position(isDragging(camera) ? drag : camera)"
      :title="`${camera.name} – drag to move`"
      @pointerdown="onMarkerPointerDown($event, camera)"
      @pointermove="onMarkerPointerMove"
      @pointerup="onMarkerPointerUp(camera)"
      @pointercancel="drag = null"
      @click="onMarkerClick(camera)"
    >
      <span class="marker-label">{{ camera.name }}</span>
    </button>

    <div v-if="editing && !editing.id" class="marker draft" :style="position(editing)" />
  </div>
</template>

<style scoped>
.barn-map {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.barn-map img {
  display: block;
  max-width: 100%;
  height: auto;
  cursor: crosshair;
  user-select: none;
}

.marker {
  position: absolute;
  width: 18px;
  height: 18px;
  padding: 0;
  border: 3px solid #fff;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 1px 4px rgb(0 0 0 / 0.5);
  transform: translate(-50%, -50%);
  cursor: grab;
  user-select: none;
  /* Let touch drags move the marker instead of scrolling the page. */
  touch-action: none;
}

.marker.dragging {
  cursor: grabbing;
  z-index: 1;
}

.marker.selected {
  background: var(--highlight);
  width: 22px;
  height: 22px;
}

.marker.draft {
  background: var(--highlight);
  border-style: dashed;
  pointer-events: none;
}

.marker-label {
  position: absolute;
  top: 100%;
  left: 50%;
  margin-top: 4px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgb(0 0 0 / 0.7);
  color: #fff;
  font-size: 12px;
  white-space: nowrap;
  transform: translateX(-50%);
  pointer-events: none;
}
</style>
