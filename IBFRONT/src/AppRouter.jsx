// src/AppRouter.jsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import SiteChrome from "./components/SiteChrome.jsx";
import Home from "./pages/Home.jsx";
import AnalyzePage from "./pages/AnalyzePage.jsx";
import About from "./pages/About.jsx";
import Docs from "./pages/Docs.jsx";
import Disclaimer from "./pages/Disclaimer.jsx";
import NotFound from "./pages/NotFound.jsx";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <SiteChrome>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/analyze" element={<AnalyzePage />} />
          <Route path="/about" element={<About />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="/disclaimer" element={<Disclaimer />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </SiteChrome>
    </BrowserRouter>
  );
}
