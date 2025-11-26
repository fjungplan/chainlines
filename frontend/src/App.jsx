import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <div className="App">
        <header className="App-header">
          <h1>Cycling Team Lineage Timeline</h1>
          <nav>
            <Link to="/">Home</Link>
          </nav>
        </header>
        
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        
        <footer>
          <p>Cycling Team Lineage © 2025</p>
        </footer>
      </div>
    </BrowserRouter>
  )
}

function HomePage() {
  return (
    <div>
      <h2>Welcome to Cycling Team Lineage</h2>
      <p>Visualization and timeline coming soon...</p>
      <p>Backend API: <code>{import.meta.env.VITE_API_URL || 'http://localhost:8000'}</code></p>
    </div>
  )
}

function NotFound() {
  return (
    <div>
      <h2>404 - Page Not Found</h2>
      <Link to="/">Go Home</Link>
    </div>
  )
}

export default App
