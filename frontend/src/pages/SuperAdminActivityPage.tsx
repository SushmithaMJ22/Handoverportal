import { useEffect, useState } from 'react' 
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import api from '../api/axios'

export default function SuperAdminActivityPage() {
  const { isSuperAdmin, user } = useAuth()
  const [handovers, setHandovers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (isSuperAdmin) {
      fetchHandovers()
    }
  }, [isSuperAdmin])

  const fetchHandovers = async () => {
    try {
      setLoading(true)
      const res = await api.get('/handovers/?limit=200')
      if (res.data?.items) {
        setHandovers(res.data.items)
      } else if (Array.isArray(res.data)) {
        setHandovers(res.data)
      } else {
        setHandovers([])
      }
    } catch (err) {
      console.error('Failed to fetch handovers:', err)
      setHandovers([])
    } finally {
      setLoading(false)
    }
  }

  if (!isSuperAdmin) {
    return <Navigate to="/dashboard" />
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700, color: '#111827' }}>
          Superadmin Activity Log
        </h1>
        <p style={{ color: '#6B7280', marginTop: '4px' }}>
          View all handover activity across the system
        </p>
      </div>

      {/* Table */}
      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#F9FAFB', borderBottom: '2px solid #E5E7EB' }}>
              {['Handover ID', 'Customer Name', 'Created By', 'Created At', 'Status'].map((header) => (
                <th key={header} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 700, color: '#6B7280', letterSpacing: '0.05em' }}>
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} style={{ padding: '48px', textAlign: 'center', color: '#9CA3AF' }}>
                  Loading...
                </td>
              </tr>
            ) : handovers.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ padding: '64px', textAlign: 'center' }}>
                  <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div>
                  <p style={{ color: '#6B7280', fontSize: '16px', margin: 0 }}>
                    No handover activity found
                  </p>
                </td>
              </tr>
            ) : (
              handovers.map((handover, index) => (
                <tr
                  key={handover.id}
                  style={{
                    borderBottom: '1px solid #F3F4F6',
                    background: index % 2 === 0 ? 'white' : '#FAFAFA'
                  }}
                >
                  <td style={{ padding: '14px 16px', fontWeight: 600, color: '#111827' }}>
                    #{handover.id}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#374151', fontSize: '14px' }}>
                    {handover.customer_name}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#374151', fontSize: '14px' }}>
                    {handover.created_by_name || 'Unknown'}
                  </td>
                  <td style={{ padding: '14px 16px', color: '#6B7280', fontSize: '13px' }}>
                    {handover.created_at ? new Date(handover.created_at).toLocaleString() : '-'}
                  </td>
                  <td style={{ padding: '14px 16px' }}>
                    <span
                      style={{
                        padding: '4px 12px',
                        borderRadius: '9999px',
                        fontSize: '12px',
                        fontWeight: 600,
                        background: handover.status === 'active' ? '#D1FAE5' : '#FEE2E2',
                        color: handover.status === 'active' ? '#065F46' : '#991B1B'
                      }}
                    >
                      {handover.status?.charAt(0).toUpperCase() + handover.status?.slice(1) || 'Unknown'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
