<template>
  <v-container class="fill-height d-flex flex-column justify-center align-center">
    <h1 class="text-red font-weight-bold mb-6 blinking">RESET PROJECT ?</h1>

    <v-switch
        v-model="parameters.reset_updates"
        :true-value="1.0"
        :false-value="0.0"
        :disabled="!isProjectDir"
        color="error"
        label="YES / NO"
        inset
        size="x-large"
    ></v-switch>
  </v-container>
</template>

<script setup>
import { computed } from 'vue'
const parameters = useState('parameters')

// Logique de validation : le bouton n'est cliquable que si output_directory contient '.fraghub'
// Note: En mode web, le check se fera par une requête API, ici on simule :
const isProjectDir = computed(() => {
  return parameters.value.output_directory && parameters.value.output_directory.includes('FragHub')
})
</script>

<style scoped>
.blinking {
  animation: blink 1s linear infinite;
}
@keyframes blink {
  0% { opacity: 1; }
  50% { opacity: 0.3; }
  100% { opacity: 1; }
}
</style>