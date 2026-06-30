import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { FileText, Download, Edit, ArrowLeft, Calendar, User, MapPin, Tag, Clipboard, MessageSquare, Trash2 } from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../hooks/useAuth';

const HandoverDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [handover, setHandover] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { isAdmin, isSuperAdmin } = useAuth();

  useEffect(() => {
    const fetchHandover = async () => {
      try {
        const res = await api.get(`/handovers/${id}`);
        setHandover(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchHandover();
  }, [id]);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this record?')) {
      try {
        await api.delete(`/handovers/${id}`);
        navigate('/handovers');
      } catch (e) {
        alert('Error deleting handover');
      }
    }
  };

  const handleDownload = async (docId: number, filename: string) => {
    try {
      const res = await api.get(`/handovers/${id}/documents/${docId}`);
      if (res.data.url) {
        window.open(res.data.url, '_blank');
      } else {
        // Local file response
        const response = await api.get(`/handovers/${id}/documents/${docId}`, {
          responseType: 'blob'
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
      }
    } catch (err) {
      alert('Error downloading file');
    }
  };

  if (loading) return <div>Loading...</div>;
  if (!handover) return <div>Record not found</div>;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/handovers')}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to List
        </button>
        {(isAdmin || isSuperAdmin) && (
          <div className="flex gap-3">
            <button
              onClick={handleDelete}
              className="bg-red-50 text-red-600 px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-red-100 transition-colors border border-red-200"
            >
              <Trash2 className="w-4 h-4" />
              Delete Record
            </button>
            <Link
              to={`/handovers/${id}/edit`}
              className="bg-indigo-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-indigo-700 transition-colors"
            >
              <Edit className="w-4 h-4" />
              Edit Record
            </Link>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 space-y-8">
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">{handover.customer_name}</h1>
                <p className="text-gray-500 mt-1">{handover.region} Region</p>
              </div>
              <span className="px-4 py-1.5 bg-green-100 text-green-700 rounded-full text-sm font-semibold uppercase tracking-wider">
                {handover.status}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-8 border-t pt-8">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Customer Details</h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                    <span className="text-gray-500">Contact Person</span>
                    <span className="text-gray-900 font-medium">{handover.contact_person || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                    <span className="text-gray-500">Contact Phone</span>
                    <span className="text-gray-900 font-medium">{handover.contact_phone || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-50 pb-2">
                    <span className="text-gray-500">Contact Email</span>
                    <span className="text-gray-900 font-medium">{handover.contact_email || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Technical Details</h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 text-gray-700">
                    <Tag className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Product:</span> {handover.product} / {handover.sub_product || <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs font-bold">N/A</span>}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700">
                    <MapPin className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Platform:</span> {handover.platform}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700">
                    <Clipboard className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Solution:</span> {handover.solution || <span className="px-2 py-0.5 bg-gray-100 text-gray-500 rounded text-xs font-bold">N/A</span>}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700 font-mono">
                    <FileText className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Ticket:</span> {handover.support_ticket}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-8 border-t pt-8">
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">Stakeholders</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex items-center gap-3 text-gray-700">
                    <User className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">PS Engineer:</span> {handover.ps_engineer}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700">
                    <User className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Sales Person:</span> {handover.sales_person}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700">
                    <User className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">PS Reviewer:</span> {handover.ps_reviewer}</span>
                  </div>
                  <div className="flex items-center gap-3 text-gray-700">
                    <User className="w-5 h-5 text-gray-400" />
                    <span><span className="font-medium">Support Reviewer:</span> {handover.support_reviewer}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-4 border-t pt-8">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-2">
                <MessageSquare className="w-4 h-4" />
                Remarks
              </h3>
              <p className="text-gray-700 whitespace-pre-wrap leading-relaxed bg-gray-50 p-4 rounded-lg italic">
                {handover.remarks || "No additional remarks provided."}
              </p>
            </div>
          </div>
        </div>

        {/* Sidebar / Documents */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="font-bold text-gray-900 mb-6 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              Attached Documents
            </h3>
            <div className="space-y-3">
              {handover.documents.length === 0 ? (
                <p className="text-gray-500 text-sm italic text-center py-4">No documents uploaded.</p>
              ) : (
                handover.documents.map((doc: any) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg group hover:bg-indigo-50 transition-colors">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                      <p className="text-xs text-indigo-600 font-medium mt-0.5">{doc.doc_type}</p>
                    </div>
                    <button
                      onClick={() => handleDownload(doc.id, doc.filename)}
                      className="ml-4 p-2 text-gray-400 hover:text-indigo-600 hover:bg-white rounded-lg transition-all shadow-none hover:shadow-sm"
                    >
                      <Download className="w-5 h-5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h3 className="font-bold text-gray-900 mb-2">Metadata</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Created At</span>
                <span className="text-gray-900 font-medium">{new Date(handover.created_at).toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Last Updated</span>
                <span className="text-gray-900 font-medium">{handover.updated_at ? new Date(handover.updated_at).toLocaleString() : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Created By</span>
                <span className="text-gray-900 font-medium">
                  {handover.created_by_name || `User #${handover.created_by}`}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HandoverDetail;
