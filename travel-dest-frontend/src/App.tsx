// Defines the top-level routes for the Smart Travel Planner frontend.

import { Navigate, Route, Routes } from "react-router-dom";

import { ProtectedRoute } from "./routes/ProtectedRoute";
import { ChatPage } from "./pages/ChatPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/chat" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}

export default App;
