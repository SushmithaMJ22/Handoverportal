import { useEffect, useState } from 'react';
import { Users, UserPlus, Shield, Mail, Trash2, Edit2, Check, X, Loader2, User, UserMinus, UserCheck } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/ui/ToastProvider';
import { ConfirmationModal } from '../components/ui/ConfirmationModal';

const validatePasswordStrength = (password: string): string | null => {
  if (password.length < 8) {
    return "Password must be at least 8 characters long"
  }
  if (!/[A-Z]/.test(password)) {
    return "Password must contain at least one uppercase letter"
  }
  if (!/[a-z]/.test(password)) {
    return "Password must contain at least one lowercase letter"
  }
  if (!/[0-9]/.test(password)) {
    return "Password must contain at least one digit"
  }
  if (!/[!@#$%^&*]/.test(password)) {
    return "Password must contain at least one special character (!@#$%^&*)"
  }
  return null
}

const UserManagement = () => {
  const { showSuccess, showError } = useToast();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'user'
  });
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<any>(null);
  const [deletingUser, setDeletingUser] = useState(false);

  const { isSuperAdmin } = useAuth();

  const fetchUsers = async () => {
    try {
      const res = await api.get('/users');
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    setPasswordError(null);
    
    if (!editingUser && formData.password !== formData.confirmPassword) {
      showError("Passwords do not match");
      return;
    }

    if (!editingUser) {
      const pwdErr = validatePasswordStrength(formData.password)
      if (pwdErr) { 
        setPasswordError(pwdErr)
        return 
      }
    }

    try {
      if (editingUser) {
        await api.put(`/users/${editingUser.id}?role=${formData.role}`);
        showSuccess('User role updated successfully!');
      } else {
        await api.post('/users/', {
          full_name: formData.full_name,
          username: formData.username,
          email: formData.email,
          password: formData.password,
          role: formData.role
        });
        showSuccess('User created successfully!');
      }
      setShowModal(false);
      setEditingUser(null);
      setFormData({ full_name: '', username: '', email: '', password: '', confirmPassword: '', role: 'user' });
      setPasswordError(null);
      fetchUsers();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail) 
        ? detail.map((d: any) => d.msg).join(', ') 
        : (typeof detail === 'string' ? detail : 'Error saving user');
      showError(message);
    }
  };

  const toggleActivation = async (u: any) => {
    try {
      if (u.is_active) {
        await api.put(`/users/${u.id}/deactivate`);
        showSuccess('User deactivated successfully!');
      } else {
        await api.put(`/users/${u.id}/reactivate`);
        showSuccess('User reactivated successfully!');
      }
      fetchUsers();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = Array.isArray(detail) 
        ? detail.map((d: any) => d.msg).join(', ') 
        : (typeof detail === 'string' ? detail : 'Error updating user status');
      showError(message);
    }
  };

  const handleDelete = async (u: any) => {
    setShowDeleteConfirm(u);
  };

  const confirmDelete = async () => {
    if (!showDeleteConfirm) return;
    
    setDeletingUser(true);
    
    try {
      await api.delete(`/users/${showDeleteConfirm.id}`);
      showSuccess('User deleted successfully!');
      fetchUsers();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const message = typeof detail === 'string' ? detail : 'Error deleting user';
      showError(message);
    } finally {
      setDeletingUser(false);
      setShowDeleteConfirm(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Users className="w-6 h-6 text-indigo-600" />
          User Management
        </h2>
        {isSuperAdmin && (
          <button
            onClick={() => {
              setEditingUser(null);
              setFormData({ full_name: '', username: '', email: '', password: '', confirmPassword: '', role: 'user' });
              setPasswordError(null);
              setShowModal(true);
            }}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-colors"
          >
            <UserPlus className="w-5 h-5" />
            Create New User
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 text-gray-500 text-sm uppercase">
            <tr>
              <th className="px-6 py-4 font-semibold">Full Name</th>
              <th className="px-6 py-4 font-semibold">Username</th>
              <th className="px-6 py-4 font-semibold">Email</th>
              <th className="px-6 py-4 font-semibold">Role</th>
              <th className="px-6 py-4 font-semibold">Status</th>
              <th className="px-6 py-4 font-semibold">Created Date</th>
              <th className="px-6 py-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-gray-500">Loading...</td></tr>
            ) : (
              users.map((u: any) => (
                <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {u.full_name || <span className="italic text-gray-400">—</span>}
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">
                    {u.username}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {u.email}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-md text-xs font-bold uppercase tracking-wider ${
                      u.role === 'super_admin' ? 'bg-purple-100 text-purple-700' :
                      u.role === 'admin' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {u.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {u.is_active ? (
                      <span className="flex items-center gap-1.5 text-sm text-green-600 font-medium">
                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                        Active
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-sm text-red-600 font-medium">
                        <div className="w-1.5 h-1.5 bg-red-500 rounded-full" />
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {new Date(u.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {isSuperAdmin && (
                      <>
                        <button
                          onClick={() => {
                            setEditingUser(u);
                            setFormData({ ...formData, role: u.role });
                            setShowModal(true);
                          }}
                          className="text-indigo-600 hover:text-indigo-900 font-medium text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => toggleActivation(u)}
                          className={`font-medium text-sm ${u.is_active ? 'text-red-600 hover:text-red-900' : 'text-green-600 hover:text-green-900'}`}
                        >
                          {u.is_active ? 'Deactivate' : 'Reactivate'}
                        </button>
                        <button
                          onClick={() => handleDelete(u)}
                          disabled={deletingUser}
                          className="font-medium text-sm text-red-600 hover:text-red-900 disabled:text-gray-400 disabled:cursor-not-allowed"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full p-8">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-xl font-bold text-gray-900">
                {editingUser ? 'Edit User Role' : 'Create New User'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!editingUser && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                    <input
                      type="text"
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      placeholder="e.g. John Smith"
                      value={formData.full_name}
                      onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Username*</label>
                    <input
                      type="text"
                      required
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.username}
                      onChange={(e) => setFormData({...formData, username: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email*</label>
                    <input
                      type="email"
                      required
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Password* (min 8 chars, 1 upper, 1 lower, 1 digit, 1 special (!@#$%^&*))</label>
                    <input
                      type="password"
                      required
                      className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none ${passwordError ? 'border-red-500' : ''}`}
                      value={formData.password}
                      onChange={(e) => {
                        const newPwd = e.target.value
                        setFormData({...formData, password: newPwd})
                        setPasswordError(validatePasswordStrength(newPwd))
                      }}
                    />
                    {passwordError && (
                      <div className="text-red-500 text-xs mt-1">
                        ⚠ {passwordError}
                      </div>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Confirm Password*</label>
                    <input
                      type="password"
                      required
                      className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={formData.confirmPassword}
                      onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                    />
                  </div>
                </>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role*</label>
                <select
                  className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-2 border rounded-lg font-medium hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 transition-colors"
                >
                  {editingUser ? 'Save Changes' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmationModal
        isOpen={showDeleteConfirm !== null}
        onClose={() => setShowDeleteConfirm(null)}
        onConfirm={confirmDelete}
        title="Delete User"
        message="Are you sure you want to delete this user? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        isLoading={deletingUser}
        type="danger"
      />
    </div>
  );
};

export default UserManagement;
