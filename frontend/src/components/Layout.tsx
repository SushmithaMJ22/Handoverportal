import { useState } from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, ClipboardList, Building2, BarChart3, Users, LogOut, FileText, Menu } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const Layout = () => {
  const location = useLocation();
  const { user, logout, isSuperAdmin, displayName } = useAuth();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const menuItems = [
    { label: 'Dashboard', icon: LayoutDashboard, path: '/dashboard', roles: ['super_admin', 'admin', 'user'] },
    { label: 'Handovers', icon: ClipboardList, path: '/handovers', roles: ['super_admin', 'admin', 'user'] },
    { label: 'Customers', icon: Building2, path: '/customers', roles: ['super_admin', 'admin', 'user'] },
    { label: 'Reports', icon: BarChart3, path: '/reports', roles: ['super_admin', 'admin', 'user'] },
    { label: 'User Management', icon: Users, path: '/users', roles: ['super_admin'] },
    { label: 'Activity Log', icon: FileText, path: '/superadmin/activity', roles: ['super_admin'] },
  ];

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      {/* Sidebar */}
      {!isSuperAdmin && (
        <aside
          className={`${
            isSidebarOpen ? 'w-64' : 'w-20'
          } bg-white border-r border-gray-200 transition-all duration-300 flex flex-col z-50`}
        >
          {/* Logo Section */}
          <div className="p-6 flex items-center gap-3">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            {isSidebarOpen && <h1 className="font-bold text-gray-900 text-lg">Handover</h1>}
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 space-y-1">
            {menuItems
              .filter((item) => item.roles.includes(user?.role))
              .map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-3 py-3 rounded-lg transition-colors group ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-600'
                        : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900'
                    }`
                  }
                >
                  <item.icon
                    className={`w-5 h-5 shrink-0 ${
                      location.pathname === item.path ? 'text-indigo-600' : 'group-hover:text-gray-900'
                    }`}
                  />
                  {isSidebarOpen && <span className="font-medium">{item.label}</span>}
                </NavLink>
              ))}
          </nav>

          {/* User Section */}
          <div className="p-4 border-t border-gray-200">
            {isSidebarOpen ? (
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3 px-2">
                  <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold">
                    {displayName?.[0]?.toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-bold text-gray-900 truncate">{displayName}</p>
                    <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
                  </div>
                </div>
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium text-sm"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-10 h-10 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center font-bold">
                  {displayName?.[0]?.toUpperCase()}
                </div>
                <button
                  onClick={logout}
                  className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}
          </div>
        </aside>
      )}

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 z-40">
          <div className="flex items-center gap-4">
            {!isSuperAdmin && (
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5" />
              </button>
            )}
            <h1 className="text-xl font-bold text-gray-900 capitalize">
              {location.pathname.split('/')[1] || 'Dashboard'}
            </h1>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-gray-500">
              <span className="text-sm font-medium">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</span>
            </div>
            {isSuperAdmin && (
              <button
                onClick={logout}
                className="flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors font-medium text-sm border border-red-100"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            )}
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 overflow-y-auto p-8 bg-gray-50/50">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
