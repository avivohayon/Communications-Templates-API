import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`, config.data);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.data);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message);
    
    // Handle specific error cases
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 404) {
        throw new Error(data.detail || 'Resource not found');
      } else if (status === 400) {
        throw new Error(data.detail || 'Invalid request');
      } else if (status === 500) {
        throw new Error('Server error. Please try again later.');
      }
    } else if (error.request) {
      throw new Error('Network error. Please check your connection and ensure the backend is running.');
    }
    
    throw error;
  }
);

// Template API methods
export const templateApi = {
  /**
   * Get all templates with pagination
   * @param {number} skip - Number of records to skip
   * @param {number} limit - Maximum number of records to return
   * @returns {Promise<Array>} List of templates
   */
  getAll: async (skip = 0, limit = 100) => {
    const response = await api.get('/templates', {
      params: { skip, limit },
    });
    return response.data;
  },

  /**
   * Get template by ID
   * @param {string} id - Template UUID
   * @returns {Promise<Object>} Template object
   */
  getById: async (id) => {
    const response = await api.get(`/templates/${id}`);
    return response.data;
  },

  /**
   * Get template by name
   * @param {string} name - Template name
   * @returns {Promise<Object>} Template object
   */
  getByName: async (name) => {
    const response = await api.get(`/templates/by-name/${name}`);
    return response.data;
  },

  /**
   * Create a new template
   * @param {Object} templateData - Template data (EmailTemplateIn or SMSTemplateIn)
   * @returns {Promise<Object>} Created template
   */
  create: async (templateData) => {
    const response = await api.post('/templates', templateData);
    return response.data;
  },

  /**
   * Update an existing template
   * @param {string} id - Template UUID
   * @param {Object} templateData - Updated template data
   * @returns {Promise<Object>} Updated template
   */
  update: async (id, templateData) => {
    const response = await api.put(`/templates/${id}`, templateData);
    return response.data;
  },

  /**
   * Delete a template (soft delete)
   * @param {string} id - Template UUID
   * @returns {Promise<void>}
   */
  delete: async (id) => {
    await api.delete(`/templates/${id}`);
  },

  /**
   * Preview template rendering
   * @param {string} id - Template UUID
   * @param {Object} data - Data for rendering (e.g., { name: "John" })
   * @returns {Promise<Object>} Rendered preview
   */
  preview: async (id, data) => {
    const response = await api.post(`/templates/${id}/preview`, { data });
    return response.data;
  },
};

// Message History API methods
export const historyApi = {
  /**
   * Get message history by ID
   * @param {string} id - History record UUID
   * @returns {Promise<Object>} History record
   */
  getById: async (id) => {
    const response = await api.get(`/history/${id}`);
    return response.data;
  },

  /**
   * Query message history with filters
   * @param {Object} filters - Filter parameters
   * @returns {Promise<Array>} List of history records
   */
  query: async (filters = {}) => {
    const response = await api.get('/history', {
      params: filters,
    });
    return response.data;
  },
};

export default api;
