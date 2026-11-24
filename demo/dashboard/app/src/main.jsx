import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";

function mount() {
  const element = document.getElementById("councilflow-root");
  if (!element) return;
  createRoot(element).render(<App />);
}

if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
else mount();
