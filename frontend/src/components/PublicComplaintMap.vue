<template>
  <section class="rounded-3xl border border-slate-200 bg-white p-4 shadow-md sm:p-5">
    <div class="mb-4 flex items-start justify-between gap-3">
      <div>
        <h3 class="text-base font-semibold text-slate-900 sm:text-lg">India Complaint Map</h3>
        <p class="mt-1 text-xs text-slate-500 sm:text-sm">
          Live open-source map with pins from reported complaint coordinates.
        </p>
      </div>
      <span class="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
        {{ markers.length }} Pins
      </span>
    </div>

    <div class="relative overflow-hidden rounded-2xl border border-slate-200 bg-slate-100">
      <div ref="mapRef" class="h-[20rem] w-full sm:h-[24rem] lg:h-[28rem]"></div>

      <div v-if="loading" class="absolute inset-0 grid place-items-center bg-white/70 backdrop-blur-sm">
        <div class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 shadow">
          Loading map...
        </div>
      </div>

      <div v-else-if="!markers.length" class="absolute inset-x-4 bottom-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700 sm:text-sm">
        No complaint coordinates available yet. New geotagged reports will appear here.
      </div>
    </div>

    <div class="mt-3 flex flex-wrap gap-2 text-xs text-slate-600">
      <span class="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-1 text-amber-700">
        <span class="h-2 w-2 rounded-full bg-amber-500"></span>
        Open
      </span>
      <span class="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-emerald-700">
        <span class="h-2 w-2 rounded-full bg-emerald-500"></span>
        Resolved / Closed
      </span>
      <span class="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-rose-700">
        <span class="h-2 w-2 rounded-full bg-rose-500"></span>
        Rejected
      </span>
      <span class="inline-flex items-center gap-1 rounded-full bg-sky-50 px-2.5 py-1 text-sky-700">
        <span class="h-2 w-2 rounded-full bg-sky-500"></span>
        Other
      </span>
    </div>
  </section>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet.markercluster'

const INDIA_CENTER = [22.5937, 78.9629]
const INDIA_BOUNDS = [
  [6.0, 67.0],
  [37.8, 97.6],
]

const props = defineProps({
  markers: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const mapRef = ref(null)
let map = null
let clusterLayer = null

function markerColor(status) {
  if (["pending", "assigned", "in_progress"].includes(status)) return '#f59e0b'
  if (["resolved", "closed"].includes(status)) return '#10b981'
  if (status === 'rejected') return '#e11d48'
  return '#0ea5e9'
}

function escapeHtml(value) {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function popupContent(marker) {
  const title = escapeHtml(marker.title || `Complaint #${marker.id}`)
  const category = escapeHtml(marker.category || 'other')
  const status = escapeHtml(marker.status || 'unknown')
  const city = escapeHtml(marker.city_name || 'Unknown city')
  return `
    <div style="min-width: 180px;">
      <p style="margin:0 0 4px;font-weight:700;color:#0f172a;">${title}</p>
      <p style="margin:0;color:#334155;font-size:12px;">${category} | ${status}</p>
      <p style="margin:2px 0 0;color:#64748b;font-size:12px;">${city}</p>
    </div>
  `
}

function markerIcon(status) {
  return L.divIcon({
    className: 'public-map-pin-wrapper',
    html: `<span class="public-map-pin" style="background:${markerColor(status)}"></span>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  })
}

function drawMarkers() {
  if (!map || !clusterLayer) return

  clusterLayer.clearLayers()

  const bounds = []
  for (const item of props.markers) {
    const latitude = Number(item.latitude)
    const longitude = Number(item.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
      continue
    }

    const point = [latitude, longitude]
    bounds.push(point)

    const marker = L.marker(point, {
      icon: markerIcon(item.status),
      keyboard: true,
    }).bindPopup(popupContent(item))

    clusterLayer.addLayer(marker)
  }

  if (bounds.length === 1) {
    map.setView(bounds[0], 9)
    return
  }

  if (bounds.length > 1) {
    map.fitBounds(bounds, {
      padding: [24, 24],
      maxZoom: 11,
    })
    return
  }

  map.fitBounds(INDIA_BOUNDS, { padding: [12, 12] })
}

function initMap() {
  if (!mapRef.value || map) return

  map = L.map(mapRef.value, {
    minZoom: 4,
    maxZoom: 17,
    zoomControl: false,
    maxBounds: [
      [-5, 58],
      [42, 102],
    ],
  })

  L.control.zoom({ position: 'topright' }).addTo(map)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors',
  }).addTo(map)

  clusterLayer = L.markerClusterGroup({
    maxClusterRadius: 50,
    disableClusteringAtZoom: 13,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
  })
  map.addLayer(clusterLayer)

  map.setView(INDIA_CENTER, 5)
  drawMarkers()
}

onMounted(async () => {
  await nextTick()
  initMap()
})

watch(
  () => props.markers,
  () => {
    drawMarkers()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
    clusterLayer = null
  }
})
</script>

<style scoped>
:deep(.public-map-pin) {
  display: inline-block;
  width: 16px;
  height: 16px;
  border-radius: 9999px;
  border: 2px solid #ffffff;
  box-shadow: 0 0 0 1px #0f172a;
}
</style>
