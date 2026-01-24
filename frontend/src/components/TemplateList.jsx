import React, { useState, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import SearchFilter from './SearchFilter';

function TemplateList({
  templates,
  loading,
  onEdit,
  onDelete,
  onPreview,
  onViewHistory,
  onRefresh,
}) {
  const [expandedId, setExpandedId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [channelFilter, setChannelFilter] = useState('all');

  // Filter templates based on search and channel type
  const filteredTemplates = useMemo(() => {
    return templates.filter((template) => {
      const matchesSearch = template.name
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesChannel =
        channelFilter === 'all' || template.channel_type === channelFilter;
      return matchesSearch && matchesChannel;
    });
  }, [templates, searchTerm, channelFilter]);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const toggleExpand = (templateId) => {
    setExpandedId(expandedId === templateId ? null : templateId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div>
      {/* Search and Filter */}
      <SearchFilter
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        channelFilter={channelFilter}
        onChannelFilterChange={setChannelFilter}
        onRefresh={onRefresh}
      />

      {/* Templates Grid */}
      {filteredTemplates.length === 0 ? (
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
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No templates found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || channelFilter !== 'all'
              ? 'Try adjusting your search or filter criteria'
              : 'Get started by creating a new template'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <div key={template.id} className="card hover:shadow-lg transition-shadow">
              {/* Template Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-gray-900 truncate">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Created {formatDate(template.creation_date)}
                  </p>
                </div>
                <span
                  className={`badge ${
                    template.channel_type === 'email'
                      ? 'badge-email'
                      : 'badge-sms'
                  }`}
                >
                  {template.channel_type.toUpperCase()}
                </span>
              </div>

              {/* Template Subject (Email only) */}
              {template.channel_type === 'email' && template.subject && (
                <div className="mb-3">
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Subject
                  </label>
                  <p className="text-sm text-gray-700 mt-1 font-mono">
                    {template.subject}
                  </p>
                </div>
              )}

              {/* Template Content Preview */}
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Content
                  </label>
                  <button
                    onClick={() => toggleExpand(template.id)}
                    className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {expandedId === template.id ? 'Collapse' : 'Expand'}
                  </button>
                </div>
                <div
                  className={`overflow-hidden transition-all ${
                    expandedId === template.id ? 'max-h-96' : 'max-h-24'
                  }`}
                >
                  <SyntaxHighlighter
                    language="django"
                    style={vscDarkPlus}
                    customStyle={{
                      margin: 0,
                      borderRadius: '0.375rem',
                      fontSize: '0.75rem',
                    }}
                    showLineNumbers={expandedId === template.id}
                  >
                    {template.content}
                  </SyntaxHighlighter>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-2 pt-4 border-t border-gray-200">
                <button
                  onClick={() => onEdit(template)}
                  className="flex-1 btn btn-secondary text-sm py-1.5"
                  title="Edit template"
                >
                  <svg
                    className="w-4 h-4 inline mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                  Edit
                </button>
                <button
                  onClick={() => onPreview(template)}
                  className="flex-1 btn btn-secondary text-sm py-1.5"
                  title="Preview template"
                >
                  <svg
                    className="w-4 h-4 inline mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                  Preview
                </button>
                <button
                  onClick={() => onViewHistory(template)}
                  className="flex-1 btn btn-secondary text-sm py-1.5"
                  title="View message history"
                >
                  <svg
                    className="w-4 h-4 inline mr-1"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  History
                </button>
                <button
                  onClick={() => onDelete(template.id)}
                  className="btn btn-danger text-sm py-1.5 px-3"
                  title="Delete template"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                    />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results Count */}
      {filteredTemplates.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Showing {filteredTemplates.length} of {templates.length} templates
        </div>
      )}
    </div>
  );
}

export default TemplateList;
