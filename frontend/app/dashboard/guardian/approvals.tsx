'use client';

import React, { useState, useEffect } from 'react';
import { 
  CheckCircle, 
  XCircle, 
  Edit3, 
  AlertTriangle,
  Loader2
} from 'lucide-react';

interface PendingChange {
  id: number;
  change_type: string;
  file_path: string;
  description: string;
  reasoning: string;
  original_code: string;
  proposed_code: string;
  created_at: string;
}

export function ApprovalQueue() {
  const [changes, setChanges] = useState<PendingChange[]>([]);
  const [selectedChange, setSelectedChange] = useState<PendingChange | null>(null);
  const [loading, setLoading] = useState(false);
  const [comment, setComment] = useState('');

  useEffect(() => {
    fetchPendingChanges();
  }, []);

  const fetchPendingChanges = async () => {
    try {
      const response = await fetch('/api/v1/guardian/changes/pending');
      const data = await response.json();
      setChanges(data);
    } catch (error) {
      console.error('Error fetching pending changes:', error);
    }
  };

  const handleApprove = async (id: number) => {
    setLoading(true);
    try {
      await fetch(`/api/v1/guardian/changes/${id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved: true, comment })
      });
      await fetchPendingChanges();
      setSelectedChange(null);
      setComment('');
    } catch (error) {
      console.error('Error approving change:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async (id: number) => {
    setLoading(true);
    try {
      await fetch(`/api/v1/guardian/changes/${id}/reject`, {
        method: 'POST'
      });
      await fetchPendingChanges();
      setSelectedChange(null);
    } catch (error) {
      console.error('Error rejecting change:', error);
    } finally {
      setLoading(false);
    }
  };

  const getApprovalLevel = (type: string) => {
    const levels: Record<string, { label: string; color: string }> = {
      hotfix: { label: 'تلقائي ✅', color: 'text-green-400' },
      optimization: { label: 'تلقائي ✅', color: 'text-green-400' },
      parameter_tuning: { label: 'نصف تلقائي ⚠️', color: 'text-yellow-400' },
      logic_change: { label: 'يدوي 👤', color: 'text-blue-400' },
      new_feature: { label: 'يدوي 👤', color: 'text-blue-400' }
    };
    return levels[type] || { label: 'غير معروف', color: 'text-gray-400' };
  };

  if (selectedChange) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">مراجعة التغيير #{selectedChange.id}</h2>
          <button
            onClick={() => setSelectedChange(null)}
            className="text-gray-400 hover:text-white"
          >
            رجوع
          </button>
        </div>

        <div className="space-y-4">
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 text-yellow-400 mb-2">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-medium">مستوى الموافقة</span>
            </div>
            <p className={`text-sm ${getApprovalLevel(selectedChange.change_type).color}`}>
              {getApprovalLevel(selectedChange.change_type).label}
            </p>
          </div>

          <div>
            <p className="text-sm text-gray-400 mb-1">الوصف:</p>
            <p className="text-sm">{selectedChange.description}</p>
          </div>

          <div>
            <p className="text-sm text-gray-400 mb-1">الملف:</p>
            <p className="text-sm font-mono bg-gray-900 p-2 rounded">{selectedChange.file_path}</p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-400 mb-1">الكود الأصلي:</p>
              <pre className="text-xs bg-gray-900 p-3 rounded overflow-auto max-h-48 text-red-400">
                {selectedChange.original_code || '// غير متوفر'}
              </pre>
            </div>
            <div>
              <p className="text-sm text-gray-400 mb-1">الكود المقترح:</p>
              <pre className="text-xs bg-gray-900 p-3 rounded overflow-auto max-h-48 text-green-400">
                {selectedChange.proposed_code || '// غير متوفر'}
              </pre>
            </div>
          </div>

          <div>
            <p className="text-sm text-gray-400 mb-1">تعليق (اختياري):</p>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg p-3 text-sm focus:border-blue-500 focus:outline-none"
              rows={2}
              placeholder="أضف تعليقاً على هذا التغيير..."
            />
          </div>

          <div className="flex gap-3 pt-4">
            <button
              onClick={() => handleApprove(selectedChange.id)}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 bg-green-500/20 text-green-400 hover:bg-green-500/30 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
              موافقة
            </button>
            <button
              onClick={() => handleReject(selectedChange.id)}
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <XCircle className="w-5 h-5" />}
              رفض
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Edit3 className="w-5 h-5 text-purple-400" />
        <h2 className="text-lg font-semibold">قائمة الموافقات</h2>
      </div>

      {changes.length === 0 ? (
        <p className="text-gray-500 text-center py-8">لا توجد تغييرات بانتظار الموافقة</p>
      ) : (
        <div className="space-y-3">
          {changes.map((change) => (
            <div
              key={change.id}
              onClick={() => setSelectedChange(change)}
              className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg cursor-pointer hover:bg-gray-700 transition-colors"
            >
              <div>
                <p className="font-medium text-sm mb-1">{change.description}</p>
                <p className="text-xs text-gray-500">{change.file_path}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs ${getApprovalLevel(change.change_type).color}`}>
                  {getApprovalLevel(change.change_type).label}
                </span>
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ChevronRight({ className }: { className?: string }) {
  return (
    <svg 
      className={className} 
      fill="none" 
      stroke="currentColor" 
      viewBox="0 0 24 24"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  );
}
