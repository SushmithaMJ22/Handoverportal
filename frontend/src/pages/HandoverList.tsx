import { useEffect, useState } from 'react' 
import { useNavigate } from 'react-router-dom' 
import { useAuth } from '../hooks/useAuth' 
import api from '../api/axios' 

export default function HandoverList() { 
  const { isAdmin, isSuperAdmin } = useAuth() 
  const navigate = useNavigate() 
  const [handovers, setHandovers] = useState<any[]>([]) 
  const [total, setTotal] = useState(0) 
  const [loading, setLoading] = useState(true) 
  const [search, setSearch] = useState('') 
  const [product, setProduct] = useState('all') 

  useEffect(() => { 
    fetchHandovers() 
  }, [search, product]) 

  const fetchHandovers = async () => { 
    try { 
      setLoading(true) 
      const params = new URLSearchParams() 
      if (search) params.append('search', search) 
      if (product !== 'all') params.append('product', product) 

      const res = await api.get(`/handovers/?${params.toString()}`) 
      console.log('Handovers response:', res.data) 

      if (res.data?.items) { 
        setHandovers(res.data.items) 
        setTotal(res.data.total) 
      } else if (Array.isArray(res.data)) { 
        setHandovers(res.data) 
        setTotal(res.data.length) 
      } else { 
        setHandovers([]) 
        setTotal(0) 
      } 
    } catch (err) { 
      console.error('Failed to fetch handovers:', err) 
      setHandovers([]) 
    } finally { 
      setLoading(false) 
    } 
  } 

  const handleDelete = async (id: number) => { 
    if (!confirm('Delete this handover?')) return 
    try { 
      await api.delete(`/handovers/${id}`) 
      fetchHandovers() 
    } catch (err) { 
      alert('Failed to delete') 
    } 
  } 

  return ( 
    <div style={{ padding: '24px' }}> 

      {/* Header */} 
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}> 
        <div style={{ display: 'flex', gap: '12px', flex: 1 }}> 
          <input 
            type="text" 
            placeholder="Search customer, ticket, engineer..." 
            value={search} 
            onChange={e => setSearch(e.target.value)} 
            style={{ 
              width: '320px', height: '40px', 
              border: '1px solid #E5E7EB', borderRadius: '8px', 
              padding: '0 12px', fontSize: '14px' 
            }} 
          /> 
          <select 
            value={product} 
            onChange={e => setProduct(e.target.value)} 
            style={{ 
              height: '40px', border: '1px solid #E5E7EB', 
              borderRadius: '8px', padding: '0 12px', fontSize: '14px' 
            }} 
          > 
            <option value="all">All Products</option> 
            <option value="AVX">AVX</option> 
            <option value="APV">APV</option> 
            <option value="vAPV">vAPV</option> 
            <option value="AG">AG</option> 
            <option value="vxAG">vxAG</option> 
            <option value="ASF">ASF</option> 
          </select> 
        </div> 
        <div style={{ display: 'flex', gap: '8px' }}> 
          <button 
            onClick={() => api.get('/reports/export?format=csv').then(() => {})} 
            style={{ 
              height: '40px', padding: '0 16px', 
              background: 'white', border: '1px solid #E5E7EB', 
              borderRadius: '8px', cursor: 'pointer', fontSize: '14px' 
            }} 
          > 
            ⬇ Export 
          </button> 
          {(isAdmin || isSuperAdmin) && ( 
            <button 
              onClick={() => navigate('/handovers/new')} 
              style={{ 
                height: '40px', padding: '0 20px', 
                background: 'linear-gradient(135deg, #4F46E5, #7C3AED)', 
                color: 'white', border: 'none', 
                borderRadius: '8px', cursor: 'pointer', 
                fontSize: '14px', fontWeight: 600 
              }} 
            > 
              + New Handover 
            </button> 
          )} 
        </div> 
      </div> 

      {/* Table */} 
      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', overflow: 'hidden' }}> 
        <table style={{ width: '100%', borderCollapse: 'collapse' }}> 
          <thead> 
            <tr style={{ background: '#F9FAFB', borderBottom: '2px solid #E5E7EB' }}> 
              {['CUSTOMER', 'REGION', 'PRODUCT', 'ENGINEER', 'TICKET', 'DATE', 'ACTIONS'].map(h => ( 
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', fontWeight: 700, color: '#6B7280', letterSpacing: '0.05em' }}> 
                  {h} 
                </th> 
              ))} 
            </tr> 
          </thead> 
          <tbody> 
            {loading ? ( 
              <tr><td colSpan={7} style={{ padding: '48px', textAlign: 'center', color: '#9CA3AF' }}>Loading...</td></tr> 
            ) : handovers.length === 0 ? ( 
              <tr> 
                <td colSpan={7} style={{ padding: '64px', textAlign: 'center' }}> 
                  <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div> 
                  <p style={{ color: '#6B7280', fontSize: '16px', margin: 0 }}>No handovers found</p> 
                  {(isAdmin || isSuperAdmin) && ( 
                    <button 
                      onClick={() => navigate('/handovers/new')} 
                      style={{ 
                        marginTop: '16px', padding: '10px 24px', 
                        background: '#4F46E5', color: 'white', 
                        border: 'none', borderRadius: '8px', 
                        cursor: 'pointer', fontWeight: 600 
                      }} 
                    > 
                      Create First Handover 
                    </button> 
                  )} 
                </td> 
              </tr> 
            ) : handovers.map((h: any, i: number) => ( 
              <tr 
                key={h.id} 
                style={{ 
                  borderBottom: '1px solid #F3F4F6', 
                  background: i % 2 === 0 ? 'white' : '#FAFAFA', 
                  cursor: 'pointer' 
                }} 
                onMouseEnter={e => e.currentTarget.style.background = '#EEF2FF'} 
                onMouseLeave={e => e.currentTarget.style.background = i % 2 === 0 ? 'white' : '#FAFAFA'} 
              > 
                <td style={{ padding: '14px 16px' }}> 
                  <div style={{ fontWeight: 600, color: '#111827' }}>{h.customer_name}</div> 
                  <div style={{ fontSize: '12px', color: '#9CA3AF' }}>{h.contact_person}</div> 
                </td> 
                <td style={{ padding: '14px 16px', color: '#6B7280', fontSize: '14px' }}>{h.region}</td> 
                <td style={{ padding: '14px 16px' }}> 
                  <span style={{ background: '#EEF2FF', color: '#4F46E5', padding: '3px 10px', borderRadius: '12px', fontSize: '13px', fontWeight: 500 }}> 
                    {h.product} 
                  </span> 
                  {h.sub_product && ( 
                    <div style={{ fontSize: '11px', color: '#9CA3AF', marginTop: '2px' }}>{h.sub_product}</div> 
                  )} 
                </td> 
                <td style={{ padding: '14px 16px', fontSize: '14px', color: '#374151' }}>{h.ps_engineer}</td> 
                <td style={{ padding: '14px 16px', fontSize: '14px', color: '#374151' }}>{h.support_ticket || '-'}</td> 
                <td style={{ padding: '14px 16px', fontSize: '13px', color: '#9CA3AF' }}> 
                  {h.created_at ? new Date(h.created_at).toLocaleDateString() : '-'} 
                </td> 
                <td style={{ padding: '14px 16px' }}> 
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}> 
                    <button 
                      onClick={() => navigate(`/handovers/${h.id}`)} 
                      style={{ color: '#4F46E5', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: '14px' }} 
                    > 
                      View → 
                    </button> 
                    {(isAdmin || isSuperAdmin) && ( 
                      <> 
                        <button 
                          onClick={e => { e.stopPropagation(); navigate(`/handovers/${h.id}/edit`) }} 
                          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }} 
                        >✏️</button> 
                        <button 
                          onClick={e => { e.stopPropagation(); handleDelete(h.id) }} 
                          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }} 
                        >🗑️</button> 
                      </> 
                    )} 
                  </div> 
                </td> 
              </tr> 
            ))} 
          </tbody> 
        </table> 

        {/* Footer */} 
        {handovers.length > 0 && ( 
          <div style={{ padding: '12px 16px', borderTop: '1px solid #F3F4F6', color: '#6B7280', fontSize: '14px' }}> 
            Showing {handovers.length} of {total}  records 
          </div> 
        )} 
      </div> 
    </div> 
  ) 
} 
