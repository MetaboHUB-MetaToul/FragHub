<template>
  <v-container class="fill-height d-flex flex-column justify-center align-center">
    <v-row v-for="item in formats" :key="item.key" class="my-2" align="center">
      <v-switch
          v-model="parameters[item.key]"
          :true-value="1.0"
          :false-value="0.0"
          :label="item.label"
          color="success"
          inset
          hide-details
      ></v-switch>
    </v-row>
  </v-container>
</template>

<script setup>
const parameters = useState('parameters')
const formats = [
  { label: 'CSV', key: 'csv' },
  { label: 'MSP', key: 'msp' },
  { label: 'JSON', key: 'json' }
]
</script>