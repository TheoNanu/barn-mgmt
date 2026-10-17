<script setup>
import { onMounted, ref } from 'vue'

const props = defineProps({
  camera: { type: Object, required: true },
})
const emit = defineEmits(['save', 'delete', 'cancel', 'view'])

const name = ref(props.camera.name)
const streamUrl = ref(props.camera.stream_url)
const nameInput = ref(null)

onMounted(() => nameInput.value.focus())

function submit() {
  emit('save', { name: name.value.trim(), stream_url: streamUrl.value.trim() })
}
</script>

<template>
  <form class="camera-form" @submit.prevent="submit">
    <h2>{{ camera.id ? 'Edit camera' : 'New camera' }}</h2>
    <p v-if="!camera.id" class="hint">Click elsewhere on the map to adjust the position.</p>

    <label>
      Name
      <input ref="nameInput" v-model="name" required maxlength="100" placeholder="e.g. Stable A entrance" />
    </label>
    <label>
      Stream URL
      <input v-model="streamUrl" required placeholder="e.g. rtsp://user:password@192.168.1.50:554/stream1" />
    </label>

    <div class="actions">
      <button type="submit" class="primary">Save</button>
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button v-if="camera.id" type="button" @click="emit('view')">Live view</button>
      <button v-if="camera.id" type="button" class="danger" @click="emit('delete')">Delete</button>
    </div>
  </form>
</template>

<style scoped>
.camera-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.camera-form label {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 14px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 8px;
}

.actions .danger {
  margin-left: auto;
}
</style>
