import { Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { ExplorePage } from './pages/ExplorePage'
import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { ProjectDetailPage } from './pages/ProjectDetailPage'
import { paths } from './routes'

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path={paths.explore} element={<ExplorePage />} />
        <Route path={paths.projectPattern} element={<ProjectDetailPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}

export default App
