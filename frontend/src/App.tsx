import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import { ExplorePageCache } from "./api/explorePageCache";
import { AppShell } from "./components/AppShell";
import { ExplorePage } from "./pages/ExplorePage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { ProjectDetailPage } from "./pages/ProjectDetailPage";
import { paths } from "./routes";

function App() {
  const [exploreCache] = useState(() => new ExplorePageCache());

  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path={paths.explore} element={<ExplorePage cache={exploreCache} />} />
        <Route path={paths.projectPattern} element={<ProjectDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}

export default App;
