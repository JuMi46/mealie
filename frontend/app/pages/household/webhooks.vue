<template>
  <NuxtPage />
</template>

<script setup lang="ts">
definePageMeta({
  middleware: ["advanced-only"],
});

const route = useRoute();
const router = useRouter();

onMounted(() => {
  if (route.path === "/household/webhooks") {
    router.replace("/household/webhooks/mealplan");
  }
});
</script>
