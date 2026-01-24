import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { historyApi } from '../services/api';
import { toast } from 'react-toastify';

function MessageHistory({ templates, initialTemplateId, onClose, isModal = false }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTemplateId, setSelectedTemplateId] = useState(initialTemplateId || '');
  const [channelFilter, setChannelFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    if (selectedTemplateId || !isModal) {
      loadHistory();
    }
  }, [selectedTemplateId, channelFilter, statusFilter]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const filters = {};
      
      if (selectedTemplateId) {
        filters.template_id = selectedTemplateId;
      }
      
      if (channelFilter !== 'all') {
        filters.channel_type = channelFilter;
      }
      
      if (statusFilter !== 'all') {
        filters.status = statusFilter;
      }

      const data = await historyApi.query(filters);
      setHistory(data);
    } catch (error) {
      toast.error(`Failed to load message history: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'success':
        return 'badge-success';
      case 'failed':
        return 'badge-failed';
      case 'partial':
        return 'badge-partial';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const toggleExpand = (historyId) => {
    setExpandedId(expandedId === historyId ? null : historyId);
  };

  const content = (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Template Filter */}
          {!isModal && (
            <div>
              <label className="label">Filter by Template</label>
              <select
                value={selectedTemplateId}
                onChange={(e) => setSelectedTemplateId(e.target.value)}
                className="input"
              >
                <option value="">All Templates</option>
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} ({template.channel_type.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Channel Filter */}
          <div>
            <label className="label">Filter by Channel</label>
            <select
              value={channelFilter}
              onChange={(e) => setChannelFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Channels</option>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="label">Filter by Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input"
            >
              <option value="all">All Statuses</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
              <option value="partial">Partial</option>
            </select>
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <button onClick={loadHistory} className="btn btn-secondary" disabled={loading}>
            <svg
              className="w-4 h-4 inline mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* History List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : history.length === 0 ? (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No message history found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No messages have been sent yet, or try adjusting your filters
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((record) => (
            <div key={record.id} className="card hover:shadow-lg transition-shadow">
              {/* Header */}
              <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">
                      {record.template_name}
                    </h3>
                    <span
                      className={`badge ${
                        record.channel_type === 'email' ? 'badge-email' : 'badge-sms'
                      }`}
                    >
                      {record.channel_type.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">
                    To: <span className="font-mono">{record.recipient}</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {formatDate(record.creation_date)}
                  </p>
                </div>
                <span className={`badge ${getStatusBadgeClass(record.status)}`}>
                  {record.status.toUpperCase()}
                </span>
              </div>

              {/* Subject (Email only) */}
              {record.rendered_subject && (
                <div className="mb-3">
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Subject
                  </label>
                  <p className="text-sm text-gray-700 mt-1">{record.rendered_subject}</p>
                </div>
              )}

              {/* Rendered Content */}
              <div className="mb-3">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Rendered Content
                  </label>
                  <button
                    onClick={() => toggleExpand(record.id)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {expandedId === record.id ? 'Collapse' : 'Expand'}
                  </button>
                </div>
                <div
                  className={`overflow-hidden transition-all ${
                    expandedId === record.id ? 'max-h-96' : 'max-h-24'
                  }`}
                >
                  {record.channel_type === 'email' ? (
                    <SyntaxHighlighter
                      language="html"
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                      }}
                      showLineNumbers={expandedId === record.id}
                    >
                      {record.rendered_content}
                    </SyntaxHighlighter>
                  ) : (
                    <div className="p-3 bg-gray-100 rounded text-sm whitespace-pre-wrap">
                      {record.rendered_content}
                    </div>
                  )}
                </div>
              </div>

              {/* Error Message (if failed) */}
              {record.error_message && (
                <div className="mt-3 p-3 bg-error-50 border border-error-200 rounded">
                  <label className="text-xs font-medium text-error-700 uppercase tracking-wide">
                    Error
                  </label>
                  <p className="text-sm text-error-800 mt-1">{record.error_message}</p>
                </div>
              )}

              {/* External Message ID */}
              {record.external_message_id && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    External ID:{' '}
                    <span className="font-mono text-gray-700">{record.external_message_id}</span>
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Results Count */}
      {history.length > 0 && (
        <div className="text-center text-sm text-gray-500">
          Showing {history.length} message{history.length !== 1 ? 's' : ''}
        </div>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Message History</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
          <div className="p-6">{content}</div>
        </div>
      </div>
    );
  }

  return <div>{content}</div>;
}

export default MessageHistory;
