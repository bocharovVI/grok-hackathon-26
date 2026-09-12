import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthGate, GuestGate, ProfileGate } from "./components/gates";
import { AnketaScreen } from "./screens/AnketaScreen";
import { AuthScreen } from "./screens/AuthScreen";
import { DiagnosisScreen } from "./screens/DiagnosisScreen";
import { DocDetailScreen } from "./screens/DocDetailScreen";
import { DocsListScreen } from "./screens/DocsListScreen";
import { OverviewScreen } from "./screens/OverviewScreen";
import { SessionProvider } from "./session/SessionContext";

export default function App() {
  return (
    <SessionProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<GuestGate />}>
            <Route path="/auth" element={<AuthScreen />} />
          </Route>
          <Route element={<AuthGate />}>
            <Route path="/anketa" element={<AnketaScreen />} />
          </Route>
          <Route element={<ProfileGate />}>
            <Route path="/" element={<OverviewScreen />} />
            <Route path="/docs" element={<DocsListScreen />} />
            <Route path="/docs/:id" element={<DocDetailScreen />} />
            <Route path="/diagnosis" element={<DiagnosisScreen />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}
