import React from "react";
import ReactDOM from "react-dom/client";
import "@fontsource-variable/cairo";
import "@fontsource-variable/manrope";
import "@fontsource-variable/fraunces";
import "./index.css";
import App from "./App";
import { LanguageProvider } from "./i18n";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LanguageProvider><App /></LanguageProvider>
  </React.StrictMode>,
);
