import "@testing-library/jest-dom/vitest";

if (typeof window !== "undefined" && !window.URL.createObjectURL) {
  window.URL.createObjectURL = () => "";
}
