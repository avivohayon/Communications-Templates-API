import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import TemplateList from './components/TemplateList';
import TemplateForm from './components/TemplateForm';
import TemplatePreview from './components/TemplatePreview';
import MessageHistory from './components/MessageHistory';
import { templateApi } from './services/api';

function App() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('templates');
  const [showForm, setShowForm] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [editMode, setEditMode] = useState(false);

  // Load templates on mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      const data = await templateApi.getAll();
      setTemplates(data);
    } catch (error) {
      toast.error(`Failed to load templates: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setSelectedTemplate(null);
    setEditMode(false);
    setShowForm(true);
  };

  const handleEditTemplate = (template) => {
    setSelectedTemplate(template);
    setEditMode(true);
    setShowForm(true);
  };

  const handleDeleteTemplate = async (templateId) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await templateApi.delete(templateId);
      toast.success('Template deleted successfully');
      loadTemplates();
    } catch (error) {
      toast.error(`Failed to delete template: ${error.message}`);
    }
  };

  const handlePreviewTemplate = (template) => {
    setSelectedTemplate(template);
    setShowPreview(true);
  };

  const handleViewHistory = (template) => {
    setSelectedTemplate(template);
    setShowHistory(true);
  };

  const handleFormSubmit = async (templateData) => {
    try {
      if (editMode && selectedTemplate) {
        await templateApi.update(selectedTemplate.id, templateData);
        toast.success('Template updated successfully');
      } else {
        await templateApi.create(templateData);
        toast.success('Template created successfully');
      }
      setShowForm(false);
      loadTemplates();
    } catch (error) {
      toast.error(`Failed to save template: ${error.message}`);
      throw error;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Template Management
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                Manage message templates for Email and SMS communications
              </p>
            </div>
            <button
              onClick={handleCreateTemplate}
              className="btn btn-primary flex items-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 4v16m8-8H4"
                />
              </svg>
              Create Template
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <nav className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('templates')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'templates'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Templates
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'preview'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Preview
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === 'history'
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Message History
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'templates' && (
          <TemplateList
            templates={templates}
            loading={loading}
            onEdit={handleEditTemplate}
            onDelete={handleDeleteTemplate}
            onPreview={handlePreviewTemplate}
            onViewHistory={handleViewHistory}
            onRefresh={loadTemplates}
          />
        )}

        {activeTab === 'preview' && (
          <TemplatePreview templates={templates} />
        )}

        {activeTab === 'history' && (
          <MessageHistory templates={templates} />
        )}
      </main>

      {/* Modals */}
      {showForm && (
        <TemplateForm
          template={selectedTemplate}
          editMode={editMode}
          onSubmit={handleFormSubmit}
          onClose={() => setShowForm(false)}
        />
      )}

      {showPreview && selectedTemplate && (
        <TemplatePreview
          templates={templates}
          initialTemplate={selectedTemplate}
          onClose={() => setShowPreview(false)}
          isModal={true}
        />
      )}

      {showHistory && selectedTemplate && (
        <MessageHistory
          templates={templates}
          initialTemplateId={selectedTemplate.id}
          onClose={() => setShowHistory(false)}
          isModal={true}
        />
      )}

      {/* Toast Notifications */}
      <ToastContainer
        position="top-right"
        autoClose={3000}
        hideProgressBar={false}
        newestOnTop={true}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
      />
    </div>
  );
}

export default App;
