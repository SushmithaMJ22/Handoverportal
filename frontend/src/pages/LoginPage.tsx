import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { FileText, Loader2, User, Lock, Eye, EyeOff, CheckCircle2, AlertCircle } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../hooks/useAuth';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const message = location.state?.message;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) { 
      setError('Enter username and password'); 
      return 
    } 

    try { 
      setLoading(true); 
      setError('') 
  
      const formData = new URLSearchParams() 
      formData.append('username', username.trim()) 
      formData.append('password', password) 
  
      const response = await api.post(
        '/auth/login',
        formData.toString(),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      ) 
  
      const { access_token, refresh_token, user } = response.data
      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(user))
      login(access_token, user, refresh_token);
  
      if (user.role === 'super_admin') { 
        navigate('/create-user') 
      } else { 
        navigate('/dashboard') 
      } 
  
    } catch (err: any) { 
      const detail = err.response?.data?.detail 
      setError(typeof detail === 'string' ? detail : 'Login failed. Please check your credentials.') 
    } finally { 
      setLoading(false) 
    } 
  };

  return (
    <div className="min-h-screen flex font-['Inter']">
      {/* Left Side - Gradient & Info */}
      <div className="hidden lg:flex lg:w-[40%] bg-gradient-to-br from-indigo-600 to-purple-700 p-12 flex-col justify-center text-white relative overflow-hidden">
        {/* Subtle Background Pattern */}
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-white blur-3xl animate-pulse"></div>
          <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-white blur-3xl animate-pulse delay-1000"></div>
        </div>

        <div className="relative z-10">
          <div className="w-20 h-20 bg-white/20 rounded-2xl flex items-center justify-center mb-8 backdrop-blur-sm border border-white/30">
            <FileText className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-5xl font-extrabold mb-4 tracking-tight">Project Handover</h1>
          <p className="text-xl text-indigo-100 mb-12 font-light">Streamline your project transitions with professional documentation and tracking.</p>
          
          <div className="space-y-6">
            <div className="flex items-center gap-4 group">
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <span className="text-lg font-medium text-indigo-50">Centralized documentation hub</span>
            </div>
            <div className="flex items-center gap-4 group">
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <span className="text-lg font-medium text-indigo-50">Strict role-based access control</span>
            </div>
            <div className="flex items-center gap-4 group">
              <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition-colors">
                <CheckCircle2 className="w-6 h-6 text-emerald-400" />
              </div>
              <span className="text-lg font-medium text-indigo-50">Advanced reporting & analytics</span>
            </div>
          </div>
        </div>
        
        <div className="mt-auto relative z-10 text-indigo-200 text-sm">
          &copy; 2024 Project Handover System. All rights reserved.
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="w-full lg:w-[60%] flex items-center justify-center p-8 bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-10 border border-gray-100">
          <div className="mb-10 text-center lg:text-left">
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Welcome Back</h2>
            <p className="text-gray-500">Sign in to manage your handovers</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-6">
            {message && (
              <div className="bg-emerald-50 border-l-4 border-emerald-500 text-emerald-800 p-4 rounded-lg flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                <span className="text-sm font-medium">{message}</span>
              </div>
            )}
            
            {error && (
              <div className="bg-red-50 border-l-4 border-red-500 text-red-800 p-4 rounded-lg flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <span className="text-sm font-medium">{error}</span>
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 ml-1">Username</label>
              <div className="relative group">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-600 transition-colors">
                  <User className="w-5 h-5" />
                </div>
                <input
                  type="text"
                  required
                  className="w-full pl-11 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all placeholder:text-gray-400 font-medium"
                  placeholder="Enter your username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700 ml-1">Password</label>
              <div className="relative group">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 group-focus-within:text-indigo-600 transition-colors">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  className="w-full pl-11 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-600 outline-none transition-all placeholder:text-gray-400 font-medium"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-200 transition-all"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-bold text-lg shadow-lg shadow-indigo-200 hover:shadow-xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              {loading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-gray-500 text-sm">
              Don't have an account? <span className="text-indigo-600 font-bold cursor-help border-b border-indigo-200 hover:border-indigo-600 transition-all">Contact your administrator</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
