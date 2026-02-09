import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import StockDetails from './pages/StockDetails';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import RAGChat from './pages/RAGChat';

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/stock/:symbol" element={<StockDetails />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/ask" element={<RAGChat />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;