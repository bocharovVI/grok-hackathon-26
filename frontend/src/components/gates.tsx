import { Navigate, Outlet } from "react-router-dom";
import { useSession } from "../session/SessionContext";

export function AuthGate() {
  const { user, ready } = useSession();
  if (!ready) return <Boot />;
  if (!user) return <Navigate to="/auth" replace />;
  return <Outlet />;
}

export function ProfileGate() {
  const { user, ready } = useSession();
  if (!ready) return <Boot />;
  if (!user) return <Navigate to="/auth" replace />;
  if (!user.profileComplete) return <Navigate to="/anketa" replace />;
  return <Outlet />;
}

export function GuestGate() {
  const { user, ready } = useSession();
  if (!ready) return <Boot />;
  if (user?.profileComplete) return <Navigate to="/" replace />;
  if (user) return <Navigate to="/anketa" replace />;
  return <Outlet />;
}

function Boot() {
  return (
    <div className="grid min-h-dvh place-items-center text-muted">
      Loading…
    </div>
  );
}
