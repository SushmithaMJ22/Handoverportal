import { useState } from 'react' 
import { useNavigate } from 'react-router-dom' 
import api from '../api/axios' 
 
export default function CreateUserPage() { 
  const navigate = useNavigate() 
  const [fullName, setFullName] = useState('') 
  const [username, setUsername] = useState('') 
  const [email, setEmail] = useState('') 
  const [password, setPassword] = useState('') 
  const [confirmPassword, setConfirmPassword] = useState('') 
  const [role, setRole] = useState('') 
  const [loading, setLoading] = useState(false) 
  const [error, setError] = useState('') 
  const [success, setSuccess] = useState('') 
 
  const handleCreate = async () => { 
    setError('') 
    if (!fullName.trim()) { setError('Full name is required'); return } 
    if (!username.trim()) { setError('Username is required'); return } 
    if (!email.trim()) { setError('Email is required'); return } 
    if (password.length < 8) { setError('Password must be at least 8 characters'); return } 
    if (password !== confirmPassword) { setError('Passwords do not match'); return } 
    if (!role) { setError('Please select Admin or User role'); return } 
    try { 
      setLoading(true) 
      const token = localStorage.getItem('token') 
     await api.post('/users/', {
  full_name: fullName.trim(),
  username: username.trim(),
  email: email.trim(),
  password,
  role
})
      setSuccess(`"${username}" created successfully!`) 
      setTimeout(() => { 
        localStorage.removeItem('token') 
        localStorage.removeItem('user') 
        navigate('/login', { state: { message: `Account "${username}" created! Please log in.` } }) 
      }, 2000) 
    } catch (err: any) { 
      const detail = err.response?.data?.detail 
      setError(typeof detail === 'string' ? detail : 'Failed to create user') 
    } finally { setLoading(false) } 
  } 
 
  const cardStyle = (selected: boolean, color: string) => ({ 
    border: `2px solid ${selected ? color : '#E5E7EB'}`, 
    borderRadius: '12px', padding: '20px', cursor: 'pointer', 
    background: selected ? (color === '#4F46E5' ? '#EEF2FF' : '#F5F3FF') : 'white', 
    transition: 'all 0.2s', position: 'relative' as const 
  }) 
 
  return ( 
    <div style={{ minHeight: '100vh', background: '#F3F4F6', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px' }}> 
      <div style={{ background: 'white', borderRadius: '20px', boxShadow: '0 20px 60px rgba(0,0,0,0.1)', width: '100%', maxWidth: '620px', overflow: 'hidden' }}> 
 
        {/* Header */} 
        <div style={{ background: 'linear-gradient(135deg, #4F46E5, #7C3AED)', padding: '32px', textAlign: 'center' }}> 
          <div style={{ fontSize: '40px' }}>👥</div> 
          <h1 style={{ color: 'white', fontSize: '24px', fontWeight: 700, margin: '8px 0 0' }}>Create Team Member</h1> 
          <p style={{ color: 'rgba(255,255,255,0.8)', margin: '8px 0 0' }}>Add a new Admin or User to the system</p> 
        </div> 
 
        <div style={{ padding: '32px' }}> 
          {error && <div style={{ background: '#FEF2F2', borderLeft: '4px solid #EF4444', color: '#B91C1C', padding: '12px', borderRadius: '8px', marginBottom: '16px' }}>⚠ {error}</div>} 
          {success && <div style={{ background: '#F0FDF4', borderLeft: '4px solid #10B981', color: '#065F46', padding: '12px', borderRadius: '8px', marginBottom: '16px' }}>✓ {success}<br /><small>Redirecting to login...</small></div>} 
 
          {/* Full Name */} 
          <div style={{ marginBottom: '16px' }}> 
            <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Full Name *</label> 
            <input type="text" placeholder="e.g. John Smith" value={fullName} onChange={e => setFullName(e.target.value)} 
              style={{ width: '100%', height: '44px', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0 12px', fontSize: '15px', boxSizing: 'border-box' }} /> 
          </div> 
 
          {/* Username + Email */} 
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}> 
            <div> 
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Username *</label> 
              <input type="text" placeholder="e.g. john.smith" value={username} onChange={e => setUsername(e.target.value)} 
                style={{ width: '100%', height: '44px', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0 12px', fontSize: '15px', boxSizing: 'border-box' }} /> 
            </div> 
            <div> 
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Email *</label> 
              <input type="email" placeholder="john@company.com" value={email} onChange={e => setEmail(e.target.value)} 
                style={{ width: '100%', height: '44px', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0 12px', fontSize: '15px', boxSizing: 'border-box' }} /> 
            </div> 
          </div> 
 
          {/* Password */} 
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}> 
            <div> 
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Password *</label> 
              <input type="password" placeholder="Min 8 characters" value={password} onChange={e => setPassword(e.target.value)} 
                style={{ width: '100%', height: '44px', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0 12px', fontSize: '15px', boxSizing: 'border-box' }} /> 
            </div> 
            <div> 
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}>Confirm Password *</label> 
              <input type="password" placeholder="Repeat password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} 
                style={{ width: '100%', height: '44px', border: '1px solid #E5E7EB', borderRadius: '8px', padding: '0 12px', fontSize: '15px', boxSizing: 'border-box' }} /> 
            </div> 
          </div> 
 
          {/* Role Cards */} 
          <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '12px' }}>Select Role *</label> 
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}> 
            <div onClick={() => setRole('admin')} style={cardStyle(role === 'admin', '#4F46E5')}> 
              {role === 'admin' && <div style={{ position: 'absolute', top: '12px', right: '12px', background: '#4F46E5', color: 'white', borderRadius: '50%', width: '20px', height: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>✓</div>} 
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>🛡️</div> 
              <div style={{ fontWeight: 700, fontSize: '16px', marginBottom: '8px' }}>Admin</div> 
              <div style={{ fontSize: '13px', lineHeight: '1.8' }}> 
                <div style={{ color: '#10B981' }}>✓ Create handovers</div> 
                <div style={{ color: '#10B981' }}>✓ Edit handovers</div> 
                <div style={{ color: '#10B981' }}>✓ Delete handovers</div> 
                <div style={{ color: '#EF4444' }}>✗ No user management</div> 
              </div> 
            </div> 
            <div onClick={() => setRole('user')} style={cardStyle(role === 'user', '#7C3AED')}> 
              {role === 'user' && <div style={{ position: 'absolute', top: '12px', right: '12px', background: '#7C3AED', color: 'white', borderRadius: '50%', width: '20px', height: '20px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px' }}>✓</div>} 
              <div style={{ fontSize: '28px', marginBottom: '8px' }}>👁️</div> 
              <div style={{ fontWeight: 700, fontSize: '16px', marginBottom: '8px' }}>User</div> 
              <div style={{ fontSize: '13px', lineHeight: '1.8' }}> 
                <div style={{ color: '#10B981' }}>✓ View handovers</div> 
                <div style={{ color: '#10B981' }}>✓ Search & filter</div> 
                <div style={{ color: '#10B981' }}>✓ Export reports</div> 
                <div style={{ color: '#EF4444' }}>✗ No create/edit/delete</div> 
              </div> 
            </div> 
          </div> 
 
          {/* Buttons */} 
          <button onClick={handleCreate} disabled={loading} 
            style={{ width: '100%', height: '50px', background: loading ? '#9CA3AF' : 'linear-gradient(135deg, #4F46E5, #7C3AED)', color: 'white', border: 'none', borderRadius: '10px', fontSize: '16px', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', marginBottom: '12px' }}> 
            {loading ? '⏳ Creating...' : 'Create & Continue →'} 
          </button> 
          <button onClick={() => { localStorage.removeItem('token'); localStorage.removeItem('user'); navigate('/login') }} 
            style={{ width: '100%', height: '44px', background: 'white', color: '#6B7280', border: '1px solid #E5E7EB', borderRadius: '10px', fontSize: '14px', cursor: 'pointer' }}> 
            Skip for now → 
          </button> 
        </div> 
      </div> 
    </div> 
  ) 
} 
