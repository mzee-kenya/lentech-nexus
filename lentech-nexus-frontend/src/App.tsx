import { BrowserRouter, Routes, Route } from 'react-router-dom'

import Home from './pages/Home'
import ProjectsPage from './pages/ProjectsPage'
import IdeasPage from './pages/IdeasPage'
import DevelopersPage from './pages/DevelopersPage'
import Login from './pages/Login'
import Register from './pages/Register'
import Profile from './pages/Profile'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import DeveloperDetail from './pages/DeveloperDetail'
import ProjectDetail from './pages/ProjectDetail'
import IdeaDetail from './pages/IdeaDetail'
import ProjectCreate from './pages/ProjectCreate'
import IdeaCreate from './pages/IdeaCreate'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/new" element={<ProtectedRoute><ProjectCreate /></ProtectedRoute>} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/ideas" element={<IdeasPage />} />
          <Route path="/ideas/new" element={<ProtectedRoute><IdeaCreate /></ProtectedRoute>} />
          <Route path="/ideas/:id" element={<IdeaDetail />} />
          <Route path="/developers" element={<DevelopersPage />} />
          <Route path="/developers/:id" element={<DeveloperDetail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App