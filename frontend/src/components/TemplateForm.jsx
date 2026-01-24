import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

function TemplateForm({ template, editMode, onSubmit, onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    channel_type: 'email',
    content: '',
    subject: '',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [detectedVariables, setDetectedVariables] = useState([]);

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name || '',
        channel_type: template.channel_type || 'email',
        content: template.content || '',
        subject: template.subject || '',
      });
    }
  }, [template]);

  // Extract Jinja2 variables from content
  useEffect(() => {
    const variables = new Set();
    const regex = /\{\{\s*(\w+)\s*\}\}/g;
    let match;

    // Extract from content
    while ((match = regex.exec(formData.content)) !== null) {
      variables.add(match[1]);
    }

    // Extract from subject (email only)
    if (formData.channel_type === 'email' && formData.subject) {
      const subjectRegex = /\{\{\s*(\w+)\s*\}\}/g;
      while ((match = subjectRegex.exec(formData.subject)) !== null) {
        variables.add(match[1]);
      }
    }

    setDetectedVariables(Array.from(variables));
  }, [formData.content, formData.subject, formData.channel_type]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Template name is required';
    } else if (formData.name.length > 255) {
      newErrors.name = 'Template name must be less than 255 characters';
    }

    if (!formData.content.trim()) {
      newErrors.content = 'Template content is required';
    }

    if (formData.channel_type === 'email' && !formData.subject.trim()) {
      newErrors.subject = 'Email subject is required';
    } else if (formData.channel_type === 'email' && formData.subject.length > 500) {
      newErrors.subject = 'Subject must be less than 500 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      const submitData = {
        name: formData.name.trim(),
        channel_type: formData.channel_type,
        content: formData.content.trim(),
      };

      // Add subject for email templates
      if (formData.channel_type === 'email') {
        submitData.subject = formData.subject.trim();
      }

      await onSubmit(submitData);
    } catch (error) {
      console.error('Form submission error:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => ({
        ...prev,
        [field]: undefined,
      }));
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">
            {editMode ? 'Edit Template' : 'Create New Template'}
          </h2>
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Template Name */}
          <div>
            <label className="label">
              Template Name <span className="text-error-600">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              className={`input ${errors.name ? 'border-error-500' : ''}`}
              placeholder="e.g., welcome_email, verification_sms"
              disabled={editMode}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-error-600">{errors.name}</p>
            )}
            {editMode && (
              <p className="mt-1 text-sm text-gray-500">
                Template name cannot be changed when editing
              </p>
            )}
          </div>

          {/* Channel Type */}
          <div>
            <label className="label">
              Channel Type <span className="text-error-600">*</span>
            </label>
            <div className="flex gap-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="email"
                  checked={formData.channel_type === 'email'}
                  onChange={(e) => handleChange('channel_type', e.target.value)}
                  className="mr-2"
                  disabled={editMode}
                />
                <span className="badge badge-email">EMAIL</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  value="sms"
                  checked={formData.channel_type === 'sms'}
                  onChange={(e) => handleChange('channel_type', e.target.value)}
                  className="mr-2"
                  disabled={editMode}
                />
                <span className="badge badge-sms">SMS</span>
              </label>
            </div>
            {editMode && (
              <p className="mt-1 text-sm text-gray-500">
                Channel type cannot be changed when editing
              </p>
            )}
          </div>

          {/* Subject (Email only) */}
          {formData.channel_type === 'email' && (
            <div>
              <label className="label">
                Subject <span className="text-error-600">*</span>
              </label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => handleChange('subject', e.target.value)}
                className={`input ${errors.subject ? 'border-error-500' : ''}`}
                placeholder="e.g., Welcome {{name}}!"
              />
              {errors.subject && (
                <p className="mt-1 text-sm text-error-600">{errors.subject}</p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                Use {'{{variable}}'} for dynamic content
              </p>
            </div>
          )}

          {/* Content */}
          <div>
            <label className="label">
              Template Content <span className="text-error-600">*</span>
            </label>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {/* Textarea */}
              <div>
                <textarea
                  value={formData.content}
                  onChange={(e) => handleChange('content', e.target.value)}
                  className={`textarea min-h-[300px] font-mono text-sm ${
                    errors.content ? 'border-error-500' : ''
                  }`}
                  placeholder={
                    formData.channel_type === 'email'
                      ? '<h1>Hello {{name}}</h1>\n<p>Welcome to our service!</p>'
                      : 'Hi {{name}}! Your code is {{code}}.'
                  }
                />
                {errors.content && (
                  <p className="mt-1 text-sm text-error-600">{errors.content}</p>
                )}
              </div>

              {/* Preview */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">
                  Syntax Preview
                </div>
                <SyntaxHighlighter
                  language="django"
                  style={vscDarkPlus}
                  customStyle={{
                    margin: 0,
                    borderRadius: '0.375rem',
                    minHeight: '300px',
                  }}
                  showLineNumbers
                >
                  {formData.content || '// Enter content to see preview...'}
                </SyntaxHighlighter>
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Use Jinja2 syntax: {'{{variable}}'} for variables
            </p>
          </div>

          {/* Detected Variables */}
          {detectedVariables.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="text-sm font-medium text-blue-900 mb-2">
                Detected Variables
              </h4>
              <div className="flex flex-wrap gap-2">
                {detectedVariables.map((variable) => (
                  <code
                    key={variable}
                    className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm font-mono"
                  >
                    {'{{'} {variable} {'}}'}
                  </code>
                ))}
              </div>
              <p className="mt-2 text-xs text-blue-700">
                These variables will need to be provided when sending messages or previewing
                the template
              </p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
              disabled={submitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? (
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
                  Saving...
                </>
              ) : (
                <>{editMode ? 'Update Template' : 'Create Template'}</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default TemplateForm;
