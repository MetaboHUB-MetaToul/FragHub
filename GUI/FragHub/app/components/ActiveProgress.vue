<template>
  <div class="mt-4 pt-4 active-progress-zone">
    <div class="text-subtitle-2 font-weight-bold mb-1 text-blue-darken-4">{{ prefix }}</div>

    <v-row class="align-center mx-0">
      <v-col cols="8" class="pa-0">
        <v-progress-linear
            :model-value="progressPercent"
            height="20"
            color="blue-darken-2"
            rounded
            class="active-bar"
        ></v-progress-linear>
      </v-col>
      <v-col cols="4" class="text-right pa-0 text-caption font-weight-bold">
        {{ progressPercent.toFixed(2) }}%
      </v-col>
    </v-row>

    <div class="text-right text-caption text-grey-darken-3 mt-1">{{ suffix }}</div>
  </div>
</template>

<script setup>
defineProps({
  prefix: {
    type: String,
    required: true
  },
  progressPercent: {
    type: Number,
    required: true
  },
  suffix: {
    type: String,
    required: true
  }
})
</script>

<style scoped>
.active-progress-zone {
  border-top: 2px solid #2196F3;
  background-color: rgba(33, 150, 243, 0.05);
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
}

/* Comportement instantané (façon PyQt) */
:deep(.v-progress-linear__determinate) {
  transition: none !important;
}

.active-bar {
  border: 1px solid #1565C0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>