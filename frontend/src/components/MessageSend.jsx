import React, { useState } from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

function MessageSend({ templates }) {
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [recipients, setRecipients] = useState('');
  const [variables, setVariables] = useState({});
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState(null);

  // Extract variables from template content
  const extractVariables = (template) => {
    if (!template) return [];
    
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

    return Array.from(variableSet);
  };

  const handleTemplateSelect = (e) => {
    const templateId = e.target.value;
    const template = templates.find((t) => t.id === templateId);
    setSelectedTemplate(template || null);
    setResult(null);
    
    if (template) {
      // Initialize variables
      const vars = extractVariables(template);
      const initialVars = {};
      vars.forEach((varName) => {
        initialVars[varName] = '';
      });
      setVariables(initialVars);
    }
  };

  const handleVariableChange = (varName, value) => {
    setVariables((prev) => ({
      ...prev,
      [varName]: value,
    }));
  };

  const handleRecipientsChange = (e) => {
    setRecipients(e.target.value);
  };

  const parseRecipients = () => {
    // Split by comma, newline, or semicolon
    return recipients
      .split(/[,;\n]/)
      .map((r) => r.trim())
      .filter((r) => r.length > 0);
  };

  const handleSend = async () => {
    if (!selectedTemplate) {
      toast.error('Please select a template');
      return;
    }

    const recipientList = parseRecipients();
    if (recipientList.length === 0) {
      toast.error('Please enter at least one recipient');
      return;
    }

    // Validate all variables have values
    const emptyVars = Object.entries(variables)
      .filter(([, value]) => !value.trim())
      .map(([key]) => key);

    if (emptyVars.length > 0) {
      toast.error(`Please fill in all variables: ${emptyVars.join(', ')}`);
      return;
    }

    setSending(true);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/messages/send`, {
        template_id: selectedTemplate.id,
        to: recipientList,
        data: variables,
      });

      setResult(response.data);
      
      const successCount = response.data.results.filter((r) => r.status === 'success').length;
      const failCount = response.data.results.filter((r) => r.status !== 'success').length;
      
      if (failCount === 0) {
        toast.success(`✅ Successfully sent ${successCount} message(s)!`);
      } else if (successCount === 0) {
        toast.error(`❌ Failed to send all ${failCount} message(s)`);
      } else {
        toast.warning(`⚠️ Sent ${successCount}, failed ${failCount}`);
      }
    } catch (error) {
      console.error('Send error:', error);
      toast.error(`Failed to send messages: ${error.response?.data?.detail || error.message}`);
    } finally {
      setSending(false);
    }
  };

  const detectedVariables = selectedTemplate ? extractVariables(selectedTemplate) : [];

  return (
    <div className="space-y-6">
      {/* Template Selection */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Select Template
        </h3>
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

            {selectedTemplate.channel_type === 'email' && (
              <div className="mb-3">
                <label className="text-sm font-medium text-gray-500">Subject</label>
                <p className="text-sm text-gray-700 mt-1 font-mono">
                  {selectedTemplate.subject}
                </p>
              </div>
            )}

            <div>
              <label className="text-sm font-medium text-gray-500">Content Preview</label>
              <div className="mt-1 p-3 bg-gray-50 rounded border border-gray-200 max-h-32 overflow-y-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {selectedTemplate.content}
                </pre>
              </div>
            </div>
          </div>

          {/* Recipients */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Recipients
            </h3>
            <label className="label">
              {selectedTemplate.channel_type === 'email' ? 'Email Addresses' : 'Phone Numbers'}
            </label>
            <textarea
              value={recipients}
              onChange={handleRecipientsChange}
              className="textarea min-h-[100px]"
              placeholder={
                selectedTemplate.channel_type === 'email'
                  ? 'Enter email addresses (one per line or comma-separated):\naviv@example.com\ntest@example.com'
                  : 'Enter phone numbers (one per line or comma-separated):\n+1234567890\n+9876543210'
              }
            />
            <p className="mt-2 text-sm text-gray-500">
              {parseRecipients().length} recipient(s) entered
            </p>
          </div>

          {/* Variables */}
          {detectedVariables.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Template Variables
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {detectedVariables.map((varName) => (
                  <div key={varName}>
                    <label className="label">
                      <code className="font-mono text-sm">
                        {'{{'} {varName} {'}}'}
                      </code>
                    </label>
                    <input
                      type="text"
                      value={variables[varName] || ''}
                      onChange={(e) => handleVariableChange(varName, e.target.value)}
                      placeholder={`Enter value for ${varName}`}
                      className="input"
                    />
                  </div>
                ))}
              </div>
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                <p className="text-sm text-blue-800">
                  💡 <strong>Note:</strong> The same variable values will be used for all recipients.
                  For personalized messages, send them individually.
                </p>
              </div>
            </div>
          )}

          {/* Send Button */}
          <div className="card">
            <button
              onClick={handleSend}
              disabled={sending}
              className="btn btn-primary w-full md:w-auto text-lg py-3 px-8"
            >
              {sending ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 inline"
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
                  Sending Messages...
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
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                  Send Messages
                </>
              )}
            </button>
          </div>

          {/* Results */}
          {result && (
            <div className="card bg-gray-50 border-2 border-gray-300">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
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
                Sending Results
              </h3>

              <div className="space-y-2">
                {result.results.map((res, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded border ${
                      res.status === 'success'
                        ? 'bg-success-50 border-success-300'
                        : 'bg-error-50 border-error-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-sm">{res.recipient}</span>
                      <span
                        className={`badge ${
                          res.status === 'success' ? 'badge-success' : 'badge-failed'
                        }`}
                      >
                        {res.status === 'success' ? 'SUCCESS' : 'FAILED'}
                      </span>
                    </div>
                    {res.external_message_id && (
                      <p className="text-sm mt-1 text-gray-600">
                        Message ID: {res.external_message_id}
                      </p>
                    )}
                    {res.error_message && (
                      <p className="text-sm mt-1 text-error-700">{res.error_message}</p>
                    )}
                  </div>
                ))}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-300">
                <p className="text-sm text-gray-600">
                  <strong>Total:</strong> {result.total_recipients} recipient(s) |{' '}
                  <strong className="text-success-700">Sent:</strong> {result.successful_count} |{' '}
                  <strong className="text-error-700">Failed:</strong> {result.failed_count}
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {!selectedTemplate && (
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
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-500">
            Select a template to send messages
          </p>
        </div>
      )}
    </div>
  );
}

export default MessageSend;
