import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Save, X, Upload, FileText, Trash2, Loader2 } from 'lucide-react';
import api from '../api/axios';

const HandoverForm = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [taxonomy, setTaxonomy] = useState<any>(null);
  
  const [formData, setFormData] = useState({
    customer_name: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    region: '',
    ps_engineer: '',
    sales_person: '',
    ps_reviewer: '',
    support_ticket: '',
    support_reviewer: '',
    product: '',
    sub_product: '',
    solution: '',
    platform: '',
    remarks: '',
    status: 'active'
  });

  const [files, setFiles] = useState<any[]>([]);
  const [submitted, setSubmitted] = useState(false);

  const fetchTaxonomy = async () => {
    try {
      const res = await api.get('/meta/taxonomy');
      setTaxonomy(res.data);
    } catch (err) {
      console.error('Failed to fetch taxonomy:', err);
    }
  };

  const fetchHandover = async () => {
    try {
      const res = await api.get(`/handovers/${id}`);
      setFormData(res.data);
    } catch (err) {
      console.error('Failed to fetch handover:', err);
    }
  };

  useEffect(() => {
    fetchTaxonomy();
    if (id) {
      fetchHandover();
    }
  }, [id]);

  const handleProductChange = (e: any) => {
    const product = e.target.value;
    setFormData({
      ...formData,
      product,
      platform: '',
      sub_product: '',
      solution: ''
    });
  };

  const handlePlatformChange = (e: any) => {
    const platform = e.target.value;
    const details = taxonomy?.[formData.product]?.platforms?.[platform];
    
    setFormData({
      ...formData,
      platform,
      sub_product: '',
      solution: ''
    });
  };

  const currentPlatformDetails = formData.product && formData.platform 
    ? taxonomy?.[formData.product]?.platforms?.[formData.platform] 
    : null;

  const [error, setError] = useState('');

  // Input style — red border if empty after submit attempt: 
  const inputStyle = (value: string) => ({ 
    width: '100%', 
    height: '44px', 
    border: `1px solid ${submitted && !value?.trim() ? '#EF4444' : '#E5E7EB'}`, 
    borderRadius: '8px', 
    padding: '0 12px', 
    fontSize: '15px', 
    boxSizing: 'border-box' as const, 
    outline: 'none' 
  }) 

  const handleSave = async () => { 
    try { 
      setSubmitted(true);
      if (!formData.customer_name.trim()) { 
        setError('Customer Name is required') 
        return 
      } 
      if (!formData.region.trim()) { 
        setError('Region is required') 
        return 
      } 
      if (!formData.product) { 
        setError('Product is required') 
        return 
      } 

      setLoading(true) 
      setError('') 
  
      // Step 1: Save handover record first (without files) 
      const handoverPayload = { 
        customer_name: formData.customer_name, 
        contact_person: formData.contact_person, 
        contact_phone: formData.contact_phone, 
        contact_email: formData.contact_email, 
        region: formData.region, 
        ps_engineer: formData.ps_engineer, 
        sales_person: formData.sales_person, 
        ps_reviewer: formData.ps_reviewer, 
        support_ticket: formData.support_ticket, 
        support_reviewer: formData.support_reviewer, 
        product: formData.product, 
        sub_product: formData.sub_product || null, 
        platform: formData.platform, 
        solution: formData.solution || null, 
        remarks: formData.remarks, 
        status: formData.status 
      } 
  
      console.log('Saving handover:', handoverPayload) 
  
      const response = await api.post('/handovers/', handoverPayload) 
      const handoverId = response.data.id 
  
      // Step 2: Upload files if any 
      if (files.length > 0) { 
        for (const fileItem of files) { 
          const formDataFile = new FormData() 
          formDataFile.append('file', fileItem.file) 
          
          // Pass doc_type as query parameter in the URL 
          await api.post( 
            `/handovers/${handoverId}/documents?doc_type=${encodeURIComponent(fileItem.type)}`, 
            formDataFile, 
            { 
              headers: { 'Content-Type': 'multipart/form-data' } 
            } 
          ) 
        } 
      } 
  
      // Success 
      navigate('/handovers') 
  
    } catch (err: any) { 
      console.error('Save handover error:', err) 
      const detail = err.response?.data?.detail 
      if (Array.isArray(detail)) { 
        alert(detail.map((d: any) => `${d.loc?.join('.')}: ${d.msg}`).join('\n')) 
      } else { 
        alert(typeof detail === 'string' ? detail : 'Error saving handover: ' + err.message) 
      } 
    } finally { 
      setLoading(false) 
    } 
  } 

  const handleSubmit = (e: any) => {
    e.preventDefault();
    handleSave();
  };

  const handleFileAdd = (e: any) => {
    const newFiles = Array.from(e.target.files).map((file: any) => ({
      file,
      type: 'HO Report'
    }));
    setFiles([...files, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto space-y-8">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-6">
        <h2 className="text-xl font-bold text-gray-900 border-b pb-4">
          {id ? 'Edit Handover' : 'Create New Handover'}
        </h2>

        {/* SECTION 1 — Customer Information */}
        <div className="space-y-6">
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
          <div className="flex items-center gap-2 text-indigo-600 font-semibold mb-2">
            <span className="p-1.5 bg-indigo-50 rounded-lg">🏢</span>
            <h3>Customer Information</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-1">
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}> 
                Customer Name <span style={{ color: '#EF4444' }}>*</span> 
              </label> 
              <input 
                type="text" 
                placeholder="Enter customer name" 
                value={formData.customer_name} 
                onChange={e => setFormData({...formData, customer_name: e.target.value})} 
                style={inputStyle(formData.customer_name)} 
              /> 
              {submitted && !formData.customer_name.trim() && ( 
                <p style={{ color: '#EF4444', fontSize: '12px', margin: '4px 0 0' }}> 
                  Customer name is required 
                </p> 
              )} 
            </div>

            <div className="space-y-1">
              <label style={{ display: 'block', fontWeight: 600, fontSize: '14px', marginBottom: '6px' }}> 
                Region <span style={{ color: '#EF4444' }}>*</span> 
              </label> 
              <input 
                type="text" 
                placeholder="e.g. North America, Middle East" 
                value={formData.region} 
                onChange={e => setFormData({...formData, region: e.target.value})} 
                style={inputStyle(formData.region)} 
              /> 
              {submitted && !formData.region.trim() && ( 
                <p style={{ color: '#EF4444', fontSize: '12px', margin: '4px 0 0' }}> 
                  Region is required 
                </p> 
              )} 
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Contact Person</label>
              <input
                type="text"
                placeholder="Contact person name"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                value={formData.contact_person}
                onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
              />
            </div>

            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Contact Phone</label>
              <input
                type="text"
                placeholder="Phone number"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                value={formData.contact_phone}
                onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
              />
            </div>

            <div className="space-y-1 md:col-span-2">
              <label className="text-sm font-medium text-gray-700">Contact Email</label>
              <input
                type="email"
                placeholder="contact@company.com"
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
                value={formData.contact_email}
                onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-6 border-t">
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Support Ticket</label>
            <input
              type="text"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              value={formData.support_ticket}
              onChange={(e) => setFormData({...formData, support_ticket: e.target.value})}
            />
          </div>

          {/* Product Taxonomy */}
          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Product *</label>
            <select
              required
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white ${
                !formData.product && submitted ? 'border-red-500' : 'border-gray-300'
              }`}
              value={formData.product}
              onChange={handleProductChange}
            >
              <option value="">Select Product</option>
              {taxonomy && Object.keys(taxonomy).map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Platform</label>
            <select
              required
              disabled={!formData.product}
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white disabled:bg-gray-50"
              value={formData.platform}
              onChange={handlePlatformChange}
            >
              <option value="">Select Platform</option>
              {formData.product && taxonomy?.[formData.product]?.platforms && Object.keys(taxonomy[formData.product].platforms).map((p: string) => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>

          {currentPlatformDetails?.sub_products?.length > 0 && (
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Sub-Product</label>
              <select
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                value={formData.sub_product}
                onChange={(e) => setFormData({...formData, sub_product: e.target.value})}
              >
                <option value="">Select Sub-Product</option>
                {currentPlatformDetails.sub_products.map((p: string) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          )}

          {currentPlatformDetails?.solutions?.length > 0 && (
            <div className="space-y-1">
              <label className="text-sm font-medium text-gray-700">Solution</label>
              <select
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none bg-white"
                value={formData.solution}
                onChange={(e) => setFormData({...formData, solution: e.target.value})}
              >
                <option value="">Select Solution</option>
                {currentPlatformDetails.solutions.map((p: string) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
          )}

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">PS Engineer</label>
            <input
              type="text"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              value={formData.ps_engineer}
              onChange={(e) => setFormData({...formData, ps_engineer: e.target.value})}
            />
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium text-gray-700">Sales Person</label>
            <input
              type="text"
              className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
              value={formData.sales_person}
              onChange={(e) => setFormData({...formData, sales_person: e.target.value})}
            />
          </div>
        </div>

        <div className="space-y-1">
          <label className="text-sm font-medium text-gray-700">Remarks</label>
          <textarea
            rows={4}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none"
            value={formData.remarks}
            onChange={(e) => setFormData({...formData, remarks: e.target.value})}
          />
        </div>

        {/* File Upload */}
        <div className="space-y-4 pt-4 border-t">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Documents
          </h3>
          
          <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center hover:border-indigo-300 transition-colors cursor-pointer relative">
            <input
              type="file"
              multiple
              className="absolute inset-0 opacity-0 cursor-pointer"
              onChange={handleFileAdd}
            />
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-sm text-gray-500">Click or drag files to upload (Max 50MB per file)</p>
          </div>

          <div className="space-y-2">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-4 bg-gray-50 p-3 rounded-lg">
                <FileText className="w-5 h-5 text-indigo-500" />
                <span className="flex-1 text-sm font-medium truncate">{f.file.name}</span>
                <select
                  className="text-xs border rounded px-2 py-1 bg-white"
                  value={f.type}
                  onChange={(e) => {
                    const newFiles = [...files];
                    newFiles[i].type = e.target.value;
                    setFiles(newFiles);
                  }}
                >
                  <option value="HO Report">HO Report</option>
                  <option value="Project Signoff">Project Signoff</option>
                  <option value="Show Tech">Show Tech</option>
                  <option value="Other">Other</option>
                </select>
                <button
                  type="button"
                  onClick={() => removeFile(i)}
                  className="text-red-500 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="px-6 py-2 border rounded-lg font-medium hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="px-8 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition-colors disabled:bg-indigo-400 flex items-center gap-2"
        >
          {loading && <Loader2 className="w-5 h-5 animate-spin" />}
          <Save className="w-5 h-5" />
          Save Handover
        </button>
      </div>
    </form>
  );
};

export default HandoverForm;
