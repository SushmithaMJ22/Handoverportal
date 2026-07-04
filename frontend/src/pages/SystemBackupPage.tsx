import { useEffect, useState } from 'react';
import { 
  Database, 
  Download, 
  Trash2, 
  RefreshCw, 
  Clock, 
  HardDrive, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  Settings,
  Play,
  Download as DownloadIcon
} from 'lucide-react';
import api from '../api/axios';
import { useAuth } from '../hooks/useAuth';

interface BackupRecord {
  id: number;
  filename: string;
  file_path: string;
  size_bytes: number;
  status: string;
  backup_type: string;
  created_at: string;
  created_by: number | null;
  metadata: any;
}

interface BackupStatus {
  last_backup_date: string | null;
  next_scheduled_backup: string | null;
  total_backups: number;
  backup_location: string;
  last_backup_size: number | null;
  scheduler_enabled: boolean;
  scheduler_frequency: string;
}

const SystemBackupPage = () => {
  const { isSuperAdmin } = useAuth();
  const [status, setStatus] = useState<BackupStatus | null>(null);
  const [backups, setBackups] = useState<BackupRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [restoringBackup, setRestoringBackup] = useState<number | null>(null);
  const [showRestoreConfirm, setShowRestoreConfirm] = useState<number | null>(null);
  const [schedulerConfig, setSchedulerConfig] = useState({
    enabled: true,
    frequency: 'weekly'
  });

  const fetchStatus = async () => {
    try {
      const res = await api.get('/backup/status');
      setStatus(res.data);
    } catch (err) {
      console.error('Error fetching backup status:', err);
    }
  };

  const fetchBackups = async () => {
    try {
      const res = await api.get('/backup/list');
      setBackups(res.data);
    } catch (err) {
      console.error('Error fetching backups:', err);
    }
  };

  useEffect(() => {
    if (isSuperAdmin) {
      fetchStatus();
      fetchBackups();
      setLoading(false);
    }
  }, [isSuperAdmin]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const handleCreateBackup = async () => {
    setCreatingBackup(true);
    try {
      await api.post('/backup/create');
      await fetchStatus();
      await fetchBackups();
      alert('Backup created successfully!');
    } catch (err: any) {
      console.error('Error creating backup:', err);
      alert(err.response?.data?.detail || 'Failed to create backup');
    } finally {
      setCreatingBackup(false);
    }
  };

  const handleDownload = async (backupId: number) => {
    try {
      const response = await api.get(`/backup/download/${backupId}`, {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', backups.find(b => b.id === backupId)?.filename || 'backup.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading backup:', err);
      alert('Failed to download backup');
    }
  };

  const handleDelete = async (backupId: number) => {
    if (!confirm('Are you sure you want to delete this backup?')) return;
    
    try {
      await api.delete(`/backup/${backupId}`);
      await fetchStatus();
      await fetchBackups();
      alert('Backup deleted successfully!');
    } catch (err) {
      console.error('Error deleting backup:', err);
      alert('Failed to delete backup');
    }
  };

  const handleRestore = async (backupId: number) => {
    setShowRestoreConfirm(backupId);
  };

  const confirmRestore = async () => {
    if (showRestoreConfirm === null) return;
    
    setRestoringBackup(showRestoreConfirm);
    setShowRestoreConfirm(null);
    
    try {
      const res = await api.post('/backup/restore', { backup_id: showRestoreConfirm });
      alert(`Restore completed successfully!\n\n${res.data.message}`);
      await fetchStatus();
      await fetchBackups();
    } catch (err: any) {
      console.error('Error restoring backup:', err);
      alert(err.response?.data?.detail || 'Failed to restore backup');
    } finally {
      setRestoringBackup(null);
    }
  };

  const handleSchedulerUpdate = async () => {
    try {
      await api.put('/backup/scheduler/config', schedulerConfig);
      await fetchStatus();
      alert('Scheduler configuration updated successfully!');
    } catch (err) {
      console.error('Error updating scheduler:', err);
      alert('Failed to update scheduler configuration');
    }
  };

  if (!isSuperAdmin) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600">Only Super Admins can access the System Backup page.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Backup</h1>
          <p className="text-gray-600 mt-1">Manage system backups and restores</p>
        </div>
        <button
          onClick={handleCreateBackup}
          disabled={creatingBackup}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {creatingBackup ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Creating...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Create Backup
            </>
          )}
        </button>
      </div>

      {/* Backup Status Card */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-600" />
          Backup Status
        </h2>
        {status && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <Clock className="w-4 h-4" />
                Last Backup
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {formatDate(status.last_backup_date)}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <Calendar className="w-4 h-4" />
                Next Scheduled
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {formatDate(status.next_scheduled_backup)}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <HardDrive className="w-4 h-4" />
                Total Backups
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {status.total_backups}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <DownloadIcon className="w-4 h-4" />
                Last Size
              </div>
              <div className="text-lg font-semibold text-gray-900">
                {status.last_backup_size ? formatBytes(status.last_backup_size) : 'N/A'}
              </div>
            </div>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center gap-2 text-gray-600 text-sm mb-1">
                <Database className="w-4 h-4" />
                Location
              </div>
              <div className="text-sm font-semibold text-gray-900 truncate">
                {status.backup_location}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Automatic Backup Settings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Settings className="w-5 h-5 text-indigo-600" />
          Automatic Backup Settings
        </h2>
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={schedulerConfig.enabled}
              onChange={(e) => setSchedulerConfig({ ...schedulerConfig, enabled: e.target.checked })}
              className="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500"
            />
            <span className="text-gray-700">Enable automatic backups</span>
          </label>
          <select
            value={schedulerConfig.frequency}
            onChange={(e) => setSchedulerConfig({ ...schedulerConfig, frequency: e.target.value })}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly (7 days)</option>
            <option value="monthly">Monthly (30 days)</option>
          </select>
          <button
            onClick={handleSchedulerUpdate}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Save Settings
          </button>
        </div>
      </div>

      {/* Backup History */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-600" />
            Backup History
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Filename
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {backups.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    No backups available. Create your first backup to get started.
                  </td>
                </tr>
              ) : (
                backups.map((backup) => (
                  <tr key={backup.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {backup.filename}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(backup.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatBytes(backup.size_bytes)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                      {backup.backup_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${
                        backup.status === 'completed' 
                          ? 'bg-green-100 text-green-800' 
                          : backup.status === 'failed'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {backup.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                        {backup.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <button
                        onClick={() => handleDownload(backup.id)}
                        className="text-indigo-600 hover:text-indigo-900 p-1 hover:bg-indigo-50 rounded"
                        title="Download"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleRestore(backup.id)}
                        disabled={restoringBackup === backup.id || backup.status !== 'completed'}
                        className="text-green-600 hover:text-green-900 p-1 hover:bg-green-50 rounded disabled:text-gray-400 disabled:cursor-not-allowed"
                        title="Restore"
                      >
                        <RefreshCw className={`w-4 h-4 ${restoringBackup === backup.id ? 'animate-spin' : ''}`} />
                      </button>
                      <button
                        onClick={() => handleDelete(backup.id)}
                        className="text-red-600 hover:text-red-900 p-1 hover:bg-red-50 rounded"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Restore Confirmation Modal */}
      {showRestoreConfirm !== null && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
              <h3 className="text-lg font-semibold text-gray-900">Confirm Restore</h3>
            </div>
            <p className="text-gray-600 mb-6">
              Restoring will replace the current database and uploaded documents with the selected backup. 
              This action cannot be undone. A pre-restore backup will be created automatically.
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowRestoreConfirm(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmRestore}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Restore System
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SystemBackupPage;
