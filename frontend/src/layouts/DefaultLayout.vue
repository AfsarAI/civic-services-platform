<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <Navbar @toggle-sidebar="toggleSidebar" />
    <div class="flex flex-1">
      <Sidebar :mobile-open="isMobileSidebarOpen" @close="closeSidebar" />
      <main class="flex-1 p-4 sm:p-6 overflow-y-auto">
        <RouterView />
      </main>
    </div>
    <Footer />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RouterView } from 'vue-router'
import { useRoute } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Sidebar from '@/components/Sidebar.vue'
import Footer from '@/components/Footer.vue'

const route = useRoute()
const isMobileSidebarOpen = ref(false)

function toggleSidebar() {
  isMobileSidebarOpen.value = !isMobileSidebarOpen.value
}

function closeSidebar() {
  isMobileSidebarOpen.value = false
}

watch(
  () => route.fullPath,
  () => {
    closeSidebar()
  },
)
</script>
