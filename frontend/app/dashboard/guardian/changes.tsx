'use client';

import React, { useState, useEffect } from 'react';
import { 
  GitCommit, 
  Clock, 
  User, 
  ChevronDown, 
  ChevronUp,
  Code2
} from 'lucide-react';

interface Change {
  id: number;
  change_type: string;
  status: string;
  file_path: string;
  description: string;
  reasoning: string;
  created_at: string;
  approved_by?: string;
  approved_at?: string;
}

export function PendingChanges() {
  const [changes, setChanges] = useState<Change[]>([]);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    fetchChanges();
  }, []);

  const fetchChanges = async () => {
    try {
      const response = await fetch('/api/v1/guardian/changes/pending');
      const data = await response.json();
      setChanges(data);
    } catch (error) {
      console.error('Error fetching changes:', error);
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      hotfix: 'bg-red-500/20 text-red-400',
      optimization: 'bg-blue-500/20 text-blue-400',
      parameter_tuning: 'bg-yellow-500/20 text-yellow-400',
      logic_change: 'bg-purple-500/20 text-purple-400',
      new_feature: 'bg-green-500/20 text-green-400'
    };
    return colors[type] || 'bg-gray-500/20 text-gray-400';
  };

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      hotfix: 'إصلاح عاجل',
      optimization: 'تحسين',
      parameter_tuning: 'ضبط معاملات',
      logic_change: 'تغيير منطقي',
      new_feature: 'ميزة جديدة'
    };
    return labels[type] || type;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-yellow-400" />
          <h2 className="text-lg font-semibold">آخر التغييرات</h2>
        </div>
        <span className="text-sm text-gray-400">{changes.length} معلق</span>
      </div>

      <div className="space-y-3">
        {changes.length === 0 ? (
          <p className="text-gray-500 text-center py-4">لا توجد تغييرات معلقة</p>
        ) : (
          changes.slice(0, 5).map((change) => (
            <div
              key={change.id}
              className="bg-gray-700/50 rounded-lg p-4 cursor-pointer hover:bg-gray-700 transition-colors"
              onClick={() => setExpandedId(expandedId === change.id ? null : change.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getTypeColor(change.change_type)}`}>
                      {getTypeLabel(change.change_type)}
                    </span>
                    <span className="text-gray-400 text-sm">#{change.id}</span>
                  </div>
                  <p className="text-sm font-medium mb-1">{change.description}</p>
                  <p className="text-xs text-gray-500">{change.file_path}</p>
                </div>
                {expandedId === change.id ? (
                  <ChevronUp className="w-5 h-5 text-gray-400" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400" />
                )}
              </div>

              {expandedId === change.id && (
                <div className="mt-4 pt-4 border-t border-gray-600">
                  <div className="space-y-3">
                    <div>
                      <p className="text-xs text-gray-400 mb-1">السبب:</p>
                      <p className="text-sm text-gray-300">{change.reasoning}</p>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(change.created_at).toLocaleString('ar-SA')}
                      </span>
                      {change.approved_by && (
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {change.approved_by}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
