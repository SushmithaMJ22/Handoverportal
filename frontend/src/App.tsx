import { Routes, Route, Navigate } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import HandoverList from './pages/HandoverList';
import HandoverDetail from './pages/HandoverDetail';
import HandoverForm from './pages/HandoverForm';
import ReportsPage from './pages/ReportsPage';
import UserManagement from './pages/UserManagement';
import CustomerManagement from './pages/CustomerManagement';
import CreateUserPage from './pages/CreateUserPage';
import SuperAdminActivityPage from './pages/SuperAdminActivityPage';
import SystemBackupPage from './pages/SystemBackupPage';
import Layout from './components/Layout';
import { useAuth } from './hooks/useAuth';

function ProtectedRoute({ children, roles = [] }: { children: React.ReactNode, roles?: string[] }) {
  const { user } = useAuth();
  
  if (!user) return <Navigate to="/login" />;
  
  if (roles.length > 0 && !roles.includes(user.role)) {
    if (user.role === 'super_admin') {
      return <Navigate to="/create-user" />;
    }
    return <Navigate to="/dashboard" />;
  }
  
  return <>{children}</>;
}

function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/create-user" element={
        <ProtectedRoute roles={['super_admin']}>
          <CreateUserPage />
        </ProtectedRoute>
      } />
      <Route path="/" element={<Layout />}>
        <Route index element={
          user?.role === 'super_admin' 
            ? <Navigate to="/dashboard" replace /> 
            : <Navigate to="/dashboard" replace />
        } />
        <Route path="dashboard" element={
          <ProtectedRoute roles={['admin', 'user', 'super_admin']}>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="handovers" element={
          <ProtectedRoute>
            <HandoverList />
          </ProtectedRoute>
        } />
        <Route path="handovers/new" element={
          <ProtectedRoute roles={['admin']}>
            <HandoverForm />
          </ProtectedRoute>
        } />
        <Route path="handovers/:id" element={
          <ProtectedRoute>
            <HandoverDetail />
          </ProtectedRoute>
        } />
        <Route path="handovers/:id/edit" element={
          <ProtectedRoute roles={['admin']}>
            <HandoverForm />
          </ProtectedRoute>
        } />
        <Route path="customers" element={
          <ProtectedRoute>
            <CustomerManagement />
          </ProtectedRoute>
        } />
        <Route path="reports" element={
          <ProtectedRoute>
            <ReportsPage />
          </ProtectedRoute>
        } />
        <Route path="users" element={
          <ProtectedRoute roles={['super_admin']}>
            <UserManagement />
          </ProtectedRoute>
        } />
        <Route path="superadmin/activity" element={
          <ProtectedRoute roles={['super_admin']}>
            <SuperAdminActivityPage />
          </ProtectedRoute>
        } />
        <Route path="system-backup" element={
          <ProtectedRoute roles={['super_admin']}>
            <SystemBackupPage />
          </ProtectedRoute>
        } />
      </Route>
      <Route path="*" element={
        user?.role === 'super_admin' 
          ? <Navigate to="/create-user" replace /> 
          : <Navigate to="/dashboard" replace />
      } />
    </Routes>
  );
}

export default App;
