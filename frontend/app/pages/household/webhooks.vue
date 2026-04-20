<template>
  <div />
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ["advanced-only"],
});

const router = useRouter();
onMounted(() => {
  router.replace("/household/webhooks/mealplan");
});
</script>
