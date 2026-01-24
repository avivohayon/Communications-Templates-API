import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { templateApi } from '../services/api';
import { toast } from 'react-toastify';

function TemplatePreview({ templates, initialTemplate, onClose, isModal = false }) {
  const [selectedTemplate, setSelectedTemplate] = useState(initialTemplate || null);
  const [variables, setVariables] = useState({});
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (selectedTemplate) {
      extractVariables(selectedTemplate);
      setPreview(null);
      setError(null);
    }
  }, [selectedTemplate]);

  const extractVariables = (template) => {
    const variableSet = new Set();
    const regex = /\{\{\s*(\w+)\s*\}\}/g;
    let match;

    // Extract from content
    while ((match = regex.exec(template.content)) !== null) {
      variableSet.add(match[1]);
    }

    // Extract from subject (email only)
    if (template.channel_type === 'email' && template.subject) {
      const subjectRegex = /\{\{\s*(\w+)\s*\}\}/g;
      while ((match = subjectRegex.exec(template.subject)) !== null) {
        variableSet.add(match[1]);
      }
    }

    // Initialize variables object
    const initialVars = {};
    Array.from(variableSet).forEach((varName) => {
      initialVars[varName] = '';
    });
    setVariables(initialVars);
  };

  const handlePreview = async () => {
    if (!selectedTemplate) {
      toast.error('Please select a template');
      return;
    }

    // Check if all variables have values
    const emptyVars = Object.entries(variables)
      .filter(([, value]) => !value.trim())
      .map(([key]) => key);

    if (emptyVars.length > 0) {
      toast.error(`Please provide values for: ${emptyVars.join(', ')}`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await templateApi.preview(selectedTemplate.id, variables);
      setPreview(result);
      toast.success('Preview generated successfully');
    } catch (err) {
      setError(err.message);
      toast.error(`Preview failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleVariableChange = (varName, value) => {
    setVariables((prev) => ({
      ...prev,
      [varName]: value,
    }));
  };

  const handleTemplateSelect = (e) => {
    const templateId = e.target.value;
    const template = templates.find((t) => t.id === templateId);
    setSelectedTemplate(template || null);
  };

  const content = (
    <div className="space-y-6">
      {/* Template Selection */}
      {!isModal && (
        <div className="card">
          <label className="label">Select Template</label>
          <select
            value={selectedTemplate?.id || ''}
            onChange={handleTemplateSelect}
            className="input"
          >
            <option value="">-- Choose a template --</option>
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name} ({template.channel_type.toUpperCase()})
              </option>
            ))}
          </select>
        </div>
      )}

      {selectedTemplate && (
        <>
          {/* Template Info */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                {selectedTemplate.name}
              </h3>
              <span
                className={`badge ${
                  selectedTemplate.channel_type === 'email'
                    ? 'badge-email'
                    : 'badge-sms'
                }`}
              >
                {selectedTemplate.channel_type.toUpperCase()}
              </span>
            </div>

            {/* Show subject for email templates */}
            {selectedTemplate.channel_type === 'email' && (
              <div className="mb-4">
                <label className="text-sm font-medium text-gray-500">Subject Template</label>
                <code className="block mt-1 p-2 bg-gray-100 rounded text-sm font-mono">
                  {selectedTemplate.subject}
                </code>
              </div>
            )}

            {/* Show content template */}
            <div>
              <label className="text-sm font-medium text-gray-500">Content Template</label>
              <SyntaxHighlighter
                language="django"
                style={vscDarkPlus}
                customStyle={{
                  marginTop: '0.25rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              >
                {selectedTemplate.content}
              </SyntaxHighlighter>
            </div>
          </div>

          {/* Variable Inputs */}
          {Object.keys(variables).length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Template Variables
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(variables).map(([varName, value]) => (
                  <div key={varName}>
                    <label className="label">
                      <code className="font-mono text-sm">
                        {'{{'} {varName} {'}}'}
                      </code>
                    </label>
                    <input
                      type="text"
                      value={value}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      placeholder={`Enter value for ${varName}`}
                      className="input"
                    />
                  </div>
                ))}
              </div>
              <div className="mt-4">
                <button
                  onClick={handlePreview}
                  disabled={loading}
                  className="btn btn-primary w-full md:w-auto"
                >
                  {loading ? (
                    <>
                      <svg
                        className="animate-spin -ml-1 mr-2 h-4 w-4 inline"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Generating Preview...
                    </>
                  ) : (
                    <>
                      <svg
                        className="w-5 h-5 inline mr-2"
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
                      Generate Preview
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Preview Result */}
          {preview && (
            <div className="card bg-success-50 border-2 border-success-200">
              <h3 className="text-lg font-semibold text-success-900 mb-4 flex items-center">
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Preview Result
              </h3>

              {/* Rendered Subject (Email only) */}
              {preview.rendered_subject && (
                <div className="mb-4">
                  <label className="text-sm font-medium text-gray-700">
                    Rendered Subject
                  </label>
                  <div className="mt-1 p-3 bg-white rounded border border-success-300">
                    <p className="text-gray-900 font-medium">{preview.rendered_subject}</p>
                  </div>
                </div>
              )}

              {/* Rendered Content */}
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Rendered Content
                </label>
                {selectedTemplate.channel_type === 'email' ? (
                  <SyntaxHighlighter
                    language="html"
                    style={vscDarkPlus}
                    customStyle={{
                      marginTop: '0.25rem',
                      borderRadius: '0.375rem',
                    }}
                  >
                    {preview.rendered_content}
                  </SyntaxHighlighter>
                ) : (
                  <div className="mt-1 p-3 bg-white rounded border border-success-300">
                    <p className="text-gray-900 whitespace-pre-wrap">
                      {preview.rendered_content}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="card bg-error-50 border-2 border-error-200">
              <h3 className="text-lg font-semibold text-error-900 mb-2 flex items-center">
                <svg
                  className="w-5 h-5 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                Preview Error
              </h3>
              <p className="text-error-800">{error}</p>
            </div>
          )}
        </>
      )}

      {!selectedTemplate && !isModal && (
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
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-500">
            Select a template to preview its rendering
          </p>
        </div>
      )}
    </div>
  );

  if (isModal) {
    return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Template Preview</h2>
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

export default TemplatePreview;
