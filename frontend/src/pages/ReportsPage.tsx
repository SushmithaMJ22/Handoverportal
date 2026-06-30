import { useState } from 'react';
import { BarChart3, Download, FileText, Table as TableIcon, Calendar, Loader2 } from 'lucide-react';
import api from '../api/axios';

const ReportsPage = () => {
  const [period, setPeriod] = useState('30d');
  const [loading, setLoading] = useState(false);

  const handleExport = async (format: string) => { 
    try { 
      const token = localStorage.getItem('token') 
      const response = await fetch(`/api/reports/export?period=${period}&format=${format}`, {
  headers: {
    Authorization: `Bearer ${localStorage.getItem('token')}`
  }
})
  
      if (!response.ok) { 
        const err = await response.json() 
        throw new Error(err.detail || 'Export failed') 
      } 
  
      const blob = await response.blob() 
      const url = window.URL.createObjectURL(blob) 
      const a = document.createElement('a') 
      a.href = url 
      a.download = `handover_report_${period}.${format === 'xlsx' ? 'xlsx' : format}` 
      document.body.appendChild(a) 
      a.click() 
      window.URL.revokeObjectURL(url) 
      document.body.removeChild(a) 
  
    } catch (err: any) { 
      alert(err.message || 'Error generating report') 
    } 
  } 

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-600" />
          Export Handover Reports
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-4">
            <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider block">Select Period</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: 'Last 7 Days', value: '7d' },
                { label: 'Last 30 Days', value: '30d' },
                { label: 'Quarter to Date', value: 'qtd' },
                { label: 'Year to Date', value: 'ytd' }
              ].map((p) => (
                <button
                  key={p.value}
                  onClick={() => setPeriod(p.value)}
                  className={`px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
                    period === p.value
                      ? 'bg-indigo-600 border-indigo-600 text-white shadow-md'
                      : 'bg-white border-gray-200 text-gray-600 hover:border-indigo-300 hover:text-indigo-600'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <label className="text-sm font-semibold text-gray-400 uppercase tracking-wider block">Download Format</label>
            <div className="space-y-3">
              <button
                disabled={loading}
                onClick={() => handleExport('pdf')}
                className="w-full flex items-center justify-between p-4 bg-red-50 text-red-700 rounded-xl hover:bg-red-100 transition-colors border border-red-100 group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-6 h-6" />
                  <span className="font-bold uppercase">PDF Report</span>
                </div>
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" />}
              </button>

              <button
                disabled={loading}
                onClick={() => handleExport('xlsx')}
                className="w-full flex items-center justify-between p-4 bg-green-50 text-green-700 rounded-xl hover:bg-green-100 transition-colors border border-green-100 group"
              >
                <div className="flex items-center gap-3">
                  <TableIcon className="w-6 h-6" />
                  <span className="font-bold uppercase">Excel Sheet</span>
                </div>
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" />}
              </button>

              <button
                disabled={loading}
                onClick={() => handleExport('csv')}
                className="w-full flex items-center justify-between p-4 bg-blue-50 text-blue-700 rounded-xl hover:bg-blue-100 transition-colors border border-blue-100 group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-6 h-6" />
                  <span className="font-bold uppercase">CSV Data</span>
                </div>
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5 opacity-0 group-hover:opacity-100 transition-opacity" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-6 flex gap-4">
        <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center text-white shrink-0">
          <Calendar className="w-6 h-6" />
        </div>
        <div>
          <h3 className="font-bold text-indigo-900">Automatic Reporting</h3>
          <p className="text-indigo-700 text-sm mt-1">
            Monthly summary reports are automatically generated and archived on the first of every month. 
            Admins can access the archive in the backup storage.
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReportsPage;
