import { useEffect, useState } from 'react' 
import { useNavigate } from 'react-router-dom' 
import { useAuth } from '../hooks/useAuth' 
import api from '../api/axios' 
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend 
} from 'recharts' 
 
const COLORS = ['#4F46E5', '#7C3AED', '#10B981', '#F59E0B', '#EF4444', '#3B82F6'] 
 
export default function Dashboard() { 
  const { user, isAdmin, isUser, isSuperAdmin, displayName } = useAuth() 
  const navigate = useNavigate() 
  const [stats, setStats] = useState({
    total_handovers: 0,
    this_month: 0,
    my_handovers: 0,
    open_tickets: 0,
    by_product: [],
    by_region: [],
    recent_handovers: []
  })
  const [loading, setLoading] = useState(true)
  const [allUsers, setAllUsers] = useState<any[]>([])

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    if (isSuperAdmin) {
      api.get('/users').then(res => {
        setAllUsers(Array.isArray(res.data) ? res.data : [])
      }).catch(() => {})
    }
  }, [isSuperAdmin])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const res = await api.get('/handovers/stats/dashboard')
      setStats(res.data)
    } catch (err) {
      console.error('Failed to fetch dashboard stats:', err)
    } finally {
      setLoading(false)
    }
  }

  const statCards = isSuperAdmin ? [
    {
      label: 'Total Handovers',
      value: stats.total_handovers,
      color: '#4F46E5',
      bg: '#EEF2FF',
      icon: '📋'
    },
    {
      label: 'Handovers This Month',
      value: stats.this_month,
      color: '#3B82F6',
      bg: '#EFF6FF',
      icon: '📅'
    },
    {
      label: 'Total Users',
      value: allUsers.length,
      color: '#10B981',
      bg: '#ECFDF5',
      icon: '👥'
    },
    {
      label: 'Open Support Tickets',
      value: stats.open_tickets,
      color: '#F59E0B',
      bg: '#FFFBEB',
      icon: '🎫'
    }
  ] : isAdmin ? [
    {
      label: 'Total Handovers',
      value: stats.total_handovers,
      color: '#4F46E5',
      bg: '#EEF2FF',
      icon: '📋'
    },
    {
      label: 'Handovers This Month',
      value: stats.this_month,
      color: '#3B82F6',
      bg: '#EFF6FF',
      icon: '📅'
    },
    {
      label: 'My Handovers',
      value: stats.my_handovers,
      color: '#10B981',
      bg: '#ECFDF5',
      icon: '✅'
    },
    {
      label: 'Open Support Tickets',
      value: stats.open_tickets,
      color: '#F59E0B',
      bg: '#FFFBEB',
      icon: '🎫'
    }
  ] : [
    {
      label: 'Total Handovers',
      value: stats.total_handovers,
      color: '#4F46E5',
      bg: '#EEF2FF',
      icon: '📋'
    },
    {
      label: 'Handovers This Month',
      value: stats.this_month,
      color: '#3B82F6',
      bg: '#EFF6FF',
      icon: '📅'
    }
  ] 
 
  return ( 
    <div style={{ padding: '32px', background: '#F3F4F6', minHeight: '100vh' }}> 
 
      {/* Welcome Banner */} 
      <div style={{ 
        background: 'linear-gradient(135deg, #4F46E5, #7C3AED)', 
        borderRadius: '16px', 
        padding: '28px 32px', 
        marginBottom: '28px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}> 
        <div> 
          <h1 style={{ color: 'white', fontSize: '26px', fontWeight: 700, margin: 0 }}> 
            Welcome back, {displayName}! 👋 
          </h1> 
          <p style={{ color: 'rgba(255,255,255,0.8)', marginTop: '6px', fontSize: '15px' }}> 
            Here is your activity overview for today 
          </p> 
        </div> 
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}> 
          {isAdmin && ( 
            <span style={{ 
              background: 'rgba(255,255,255,0.2)', 
              color: 'white', 
              padding: '6px 18px', 
              borderRadius: '20px', 
              fontWeight: 600, 
              fontSize: '14px', 
              border: '1px solid rgba(255,255,255,0.3)' 
            }}> 
              Admin 
            </span> 
          )} 
          {isUser && ( 
            <span style={{ 
              background: 'rgba(255,255,255,0.2)', 
              color: 'white', 
              padding: '6px 18px', 
              borderRadius: '20px', 
              fontWeight: 600, 
              fontSize: '14px', 
              border: '1px solid rgba(255,255,255,0.3)' 
            }}> 
              User 
            </span> 
          )} 
        </div> 
      </div> 
 
      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '28px' }}>
        {isSuperAdmin && (
          <button
            onClick={() => navigate('/users')}
            style={{
              background: 'linear-gradient(135deg, #059669, #047857)',
              color: 'white',
              padding: '12px 28px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '15px',
              boxShadow: '0 4px 12px rgba(5,150,105,0.4)'
            }}
          >
            👥 Manage Users
          </button>
        )}
        {isSuperAdmin && (
          <button
            onClick={() => navigate('/superadmin/activity')}
            style={{
              background: 'linear-gradient(135deg, #7C3AED, #6D28D9)',
              color: 'white',
              padding: '12px 28px',
              borderRadius: '10px',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 600,
              fontSize: '15px',
              boxShadow: '0 4px 12px rgba(124,58,237,0.4)'
            }}
          >
            📊 Activity Log
          </button>
        )}
        {isAdmin && (
          <button
            onClick={() => navigate('/handovers/new')} 
            style={{ 
              background: 'linear-gradient(135deg, #4F46E5, #7C3AED)', 
              color: 'white', 
              padding: '12px 28px', 
              borderRadius: '10px', 
              border: 'none', 
              cursor: 'pointer', 
              fontWeight: 600, 
              fontSize: '15px', 
              boxShadow: '0 4px 12px rgba(79,70,229,0.4)' 
            }} 
          > 
            + Create New Handover 
          </button> 
        )} 
        {isUser && ( 
          <button 
            onClick={() => navigate('/reports')} 
            style={{ 
              background: 'linear-gradient(135deg, #4F46E5, #7C3AED)', 
              color: 'white', 
              padding: '12px 28px', 
              borderRadius: '10px', 
              border: 'none', 
              cursor: 'pointer', 
              fontWeight: 600, 
              fontSize: '15px' 
            }} 
          > 
            Export Report 
          </button> 
        )} 
        <button 
          onClick={fetchStats} 
          style={{ 
            background: 'white', 
            color: '#4F46E5', 
            padding: '12px 20px', 
            borderRadius: '10px', 
            border: '1px solid #4F46E5', 
            cursor: 'pointer', 
            fontWeight: 600, 
            fontSize: '15px' 
          }} 
        > 
          🔄 Refresh 
        </button> 
      </div> 
 
      {/* Stats Cards */} 
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', 
        gap: '20px', 
        marginBottom: '28px' 
      }}> 
        {statCards.map((card, i) => ( 
          <div key={i} style={{ 
            background: 'white', 
            borderRadius: '14px', 
            padding: '24px', 
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)', 
            borderLeft: `4px solid ${card.color}`, 
            transition: 'transform 0.2s, box-shadow 0.2s', 
            cursor: 'default' 
          }} 
            onMouseEnter={e => { 
              e.currentTarget.style.transform = 'translateY(-2px)' 
              e.currentTarget.style.boxShadow = '0 8px 20px rgba(0,0,0,0.1)' 
            }} 
            onMouseLeave={e => { 
              e.currentTarget.style.transform = 'translateY(0)' 
              e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)' 
            }} 
          > 
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}> 
              <div> 
                <p style={{ color: '#6B7280', fontSize: '13px', margin: 0, fontWeight: 500 }}> 
                  {card.label} 
                </p> 
                <p style={{ 
                   fontSize: '36px', 
                   fontWeight: 700, 
                   margin: '8px 0 0', 
                   color: '#111827' 
                }}> 
                   {loading ? '...' : card.value} 
                </p> 
              </div> 
              <div style={{ 
                background: card.bg, 
                borderRadius: '10px', 
                width: '48px', 
                height: '48px', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                fontSize: '22px' 
              }}> 
                {card.icon} 
              </div> 
            </div> 
          </div> 
        ))} 
      </div> 
 
      {/* Charts Row */} 
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '20px', 
        marginBottom: '28px' 
      }}> 
        {/* Bar Chart - By Product */} 
        <div style={{ 
          background: 'white', 
          borderRadius: '14px', 
          padding: '24px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)' 
        }}> 
          <h3 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: 600, color: '#111827' }}> 
            Handovers by Product 
          </h3> 
          {stats.by_product.length === 0 ? ( 
            <div style={{ textAlign: 'center', padding: '40px', color: '#9CA3AF' }}> 
              No data yet 
            </div> 
          ) : ( 
            <ResponsiveContainer width="100%" height={220}> 
              <BarChart data={stats.by_product}> 
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" /> 
                <XAxis dataKey="product" tick={{ fontSize: 12 }} /> 
                <YAxis tick={{ fontSize: 12 }} /> 
                <Tooltip /> 
                <Bar dataKey="count" fill="#4F46E5" radius={[6,6,0,0]} /> 
              </BarChart> 
            </ResponsiveContainer> 
          )} 
        </div> 
 
        {/* Pie Chart - By Region */} 
        <div style={{ 
          background: 'white', 
          borderRadius: '14px', 
          padding: '24px', 
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)' 
        }}> 
          <h3 style={{ margin: '0 0 20px', fontSize: '16px', fontWeight: 600, color: '#111827' }}> 
            Handovers by Region 
          </h3> 
          {stats.by_region.length === 0 ? ( 
            <div style={{ textAlign: 'center', padding: '40px', color: '#9CA3AF' }}> 
              No data yet 
            </div> 
          ) : ( 
            <ResponsiveContainer width="100%" height={220}> 
              <PieChart> 
                <Pie 
                  data={stats.by_region} 
                  dataKey="count" 
                  nameKey="region" 
                  cx="50%" 
                  cy="50%" 
                  outerRadius={80} 
                  label={({ region, percent }) => 
                    `${region} ${(percent * 100).toFixed(0)}%` 
                  } 
                > 
                  {stats.by_region.map((_, index) => ( 
                    <Cell key={index} fill={COLORS[index % COLORS.length]} /> 
                  ))} 
                </Pie> 
                <Tooltip /> 
                <Legend /> 
              </PieChart> 
            </ResponsiveContainer> 
          )} 
        </div> 
      </div> 
 
      {/* Recent Handovers Table */} 
      <div style={{ 
        background: 'white', 
        borderRadius: '14px', 
        padding: '24px', 
        boxShadow: '0 1px 3px rgba(0,0,0,0.08)' 
      }}> 
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}> 
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#111827' }}> 
            Recent Handovers 
          </h3> 
          <button 
            onClick={() => navigate('/handovers')} 
            style={{ 
              background: 'none', 
              border: 'none', 
              color: '#4F46E5', 
              cursor: 'pointer', 
              fontWeight: 600, 
              fontSize: '14px' 
            }} 
          > 
            View All → 
          </button> 
        </div> 
        {stats.recent_handovers.length === 0 ? ( 
          <div style={{ textAlign: 'center', padding: '40px', color: '#9CA3AF' }}> 
            <p style={{ fontSize: '32px' }}>📋</p> 
            <p>No handovers yet</p> 
            {isAdmin && ( 
              <button 
                onClick={() => navigate('/handovers/new')} 
                style={{ 
                  background: '#4F46E5', 
                  color: 'white', 
                  padding: '10px 24px', 
                  borderRadius: '8px', 
                  border: 'none', 
                  cursor: 'pointer', 
                  fontWeight: 600 
                }} 
              > 
                Create First Handover 
              </button> 
            )} 
          </div> 
        ) : ( 
          <table style={{ width: '100%', borderCollapse: 'collapse' }}> 
            <thead> 
              <tr style={{ borderBottom: '2px solid #F3F4F6' }}> 
                {['#', 'Product', 'Platform', 'PS Engineer', 'Status', 'Date'].map(h => ( 
                  <th key={h} style={{ 
                    textAlign: 'left', 
                    padding: '10px 12px', 
                    fontSize: '13px', 
                    fontWeight: 600, 
                    color: '#6B7280' 
                  }}>{h}</th> 
                ))} 
              </tr> 
            </thead> 
            <tbody> 
              {stats.recent_handovers.map((h: any, i: number) => ( 
                <tr 
                  key={h.id} 
                  onClick={() => navigate(`/handovers/${h.id}`)} 
                  style={{ 
                    borderBottom: '1px solid #F9FAFB', 
                    cursor: 'pointer', 
                    background: i % 2 === 0 ? 'white' : '#FAFAFA' 
                  }} 
                  onMouseEnter={e => e.currentTarget.style.background = '#EEF2FF'} 
                  onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'white' : '#FAFAFA'} 
                > 
                  <td style={{ padding: '12px' }}>{h.id}</td> 
                  <td style={{ padding: '12px' }}> 
                    <span style={{ 
                      background: '#EEF2FF', 
                      color: '#4F46E5', 
                      padding: '3px 10px', 
                      borderRadius: '12px', 
                      fontSize: '13px', 
                      fontWeight: 500 
                    }}> 
                      {h.product || 'N/A'} 
                    </span> 
                  </td> 
                  <td style={{ padding: '12px', fontSize: '14px' }}>{h.platform || 'N/A'}</td> 
                  <td style={{ padding: '12px', fontSize: '14px' }}>{h.ps_engineer || 'N/A'}</td> 
                  <td style={{ padding: '12px' }}> 
                    <span style={{ 
                      background: h.status === 'active' ? '#ECFDF5' : '#F3F4F6', 
                      color: h.status === 'active' ? '#10B981' : '#6B7280', 
                      padding: '3px 10px', 
                      borderRadius: '12px', 
                      fontSize: '13px', 
                      fontWeight: 500 
                    }}> 
                      {h.status || 'active'} 
                    </span> 
                  </td> 
                  <td style={{ padding: '12px', fontSize: '13px', color: '#6B7280' }}> 
                    {h.created_at ? new Date(h.created_at).toLocaleDateString() : 'N/A'} 
                  </td> 
                </tr> 
              ))} 
            </tbody> 
          </table>
        )}
      </div>

      {isSuperAdmin && allUsers.length > 0 && (
        <div style={{
          background: 'white',
          borderRadius: '14px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
          marginTop: '28px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600, color: '#111827' }}>
              All Users & Admins
            </h3>
            <button
              onClick={() => navigate('/users')}
              style={{ background: 'none', border: 'none', color: '#4F46E5', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }}
            >
              Manage Users →
            </button>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #F3F4F6' }}>
                {['#', 'Full Name', 'Username', 'Email', 'Role', 'Status'].map(h => (
                  <th key={h} style={{ textAlign: 'left', padding: '10px 12px', fontSize: '13px', fontWeight: 600, color: '#6B7280' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {allUsers.map((u: any, i: number) => (
                <tr key={u.id} style={{ borderBottom: '1px solid #F9FAFB', background: i % 2 === 0 ? 'white' : '#FAFAFA' }}>
                  <td style={{ padding: '12px', fontSize: '14px' }}>{u.id}</td>
                  <td style={{ padding: '12px', fontSize: '14px', fontWeight: 500 }}>{u.full_name || '—'}</td>
                  <td style={{ padding: '12px', fontSize: '14px' }}>{u.username}</td>
                  <td style={{ padding: '12px', fontSize: '14px', color: '#6B7280' }}>{u.email}</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      background: u.role === 'super_admin' ? '#FEF3C7' : u.role === 'admin' ? '#EEF2FF' : '#F0FDF4',
                      color: u.role === 'super_admin' ? '#D97706' : u.role === 'admin' ? '#4F46E5' : '#10B981',
                      padding: '3px 10px', borderRadius: '12px', fontSize: '13px', fontWeight: 500
                    }}>
                      {u.role}
                    </span>
                  </td>
                  <td style={{ padding: '12px' }}>
                    <span style={{
                      background: u.is_active !== false ? '#ECFDF5' : '#FEF2F2',
                      color: u.is_active !== false ? '#10B981' : '#EF4444',
                      padding: '3px 10px', borderRadius: '12px', fontSize: '13px', fontWeight: 500
                    }}>
                      {u.is_active !== false ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

    </div> 
  ) 
} 
