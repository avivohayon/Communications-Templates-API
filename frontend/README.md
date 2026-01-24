# Template Management UI

A modern, responsive React application for managing message templates (Email & SMS) for the Communications API.

## Features

✅ **CRUD Operations** - Create, Read, Update, and Delete templates  
✅ **Syntax Highlighting** - Beautiful code highlighting for template content using Prism  
✅ **Live Preview** - Test template rendering with sample data before sending  
✅ **Message History** - View sent messages with filtering and search  
✅ **Search & Filter** - Find templates by name or channel type  
✅ **Responsive Design** - Works seamlessly on mobile, tablet, and desktop  
✅ **Real-time Validation** - Form validation with helpful error messages  
✅ **Variable Detection** - Automatically detects Jinja2 variables in templates  

## Prerequisites

Before running this application, ensure you have:

- **Node.js** version 18 or higher
- **npm** version 9 or higher
- **Backend API** running on `http://localhost:8000`

Check your Node.js version:
```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher
```

## Installation

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

This will install:
- React 18 - UI framework
- Axios - HTTP client for API calls
- Tailwind CSS - Utility-first CSS framework
- React Syntax Highlighter - Code syntax highlighting
- React Toastify - Toast notifications
- Vite - Fast build tool and dev server

## Running the Application

### Development Mode

Start the development server with hot reload:

```bash
npm start
```

Or:

```bash
npm run dev
```

The application will automatically open in your browser at `http://localhost:3000`

### Production Build

Build the application for production:

```bash
npm run build
```

Preview the production build:

```bash
npm run preview
```

## Backend Requirements

**IMPORTANT:** The backend API must be running before starting the frontend.

1. Start the backend server:
```bash
cd ..  # Go back to project root
python3 run_server.py
```

2. Verify the backend is running:
```bash
curl http://localhost:8000/health
```

You should see: `{"status":"healthy"}`

3. If you see a connection error in the UI, make sure:
   - The backend is running on port 8000
   - There are no firewall issues
   - CORS is properly configured

## Project Structure

```
frontend/
├── index.html              # HTML entry point
├── package.json            # Dependencies and scripts
├── vite.config.js          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── postcss.config.js       # PostCSS configuration
└── src/
    ├── index.js            # React entry point
    ├── index.css           # Global styles with Tailwind
    ├── App.jsx             # Main application component
    ├── components/         # React components
    │   ├── TemplateList.jsx      # Templates grid display
    │   ├── TemplateForm.jsx      # Create/Edit form
    │   ├── TemplatePreview.jsx   # Live preview
    │   ├── MessageHistory.jsx    # History viewer
    │   └── SearchFilter.jsx      # Search and filter UI
    └── services/
        └── api.js          # API service layer (Axios)
```

## Component Descriptions

### App.jsx
Main application container that manages:
- Global state (templates, selected template, modals)
- Tab navigation (Templates, Preview, History)
- API calls coordination
- Toast notifications

### TemplateList.jsx
Displays all templates in a responsive grid with:
- Search and filter integration
- Expandable content preview
- Action buttons (Edit, Delete, Preview, History)
- Syntax highlighting for template content
- Empty state handling

### TemplateForm.jsx
Create and edit template form with:
- Dynamic fields based on channel type
- Real-time Jinja2 variable detection
- Syntax highlighting preview
- Form validation
- Email: name, subject, content
- SMS: name, content

### TemplatePreview.jsx
Live template preview with:
- Template selection dropdown
- Dynamic variable input fields
- Real-time rendering via API
- Syntax-highlighted output
- Error handling for missing variables

### MessageHistory.jsx
View sent messages with:
- Filter by template, channel, and status
- Status badges (success, failed, partial)
- Expandable rendered content
- Syntax highlighting for email content
- Error messages display

### SearchFilter.jsx
Search and filter controls with:
- Debounced search (300ms)
- Channel type filter
- Active filters display
- Clear filters button
- Refresh button

## API Configuration

The application connects to the backend API at `http://localhost:8000` by default.

To use a different API URL, set the `VITE_API_URL` environment variable:

```bash
# Create a .env file in the frontend directory
echo "VITE_API_URL=http://your-api-url:8000" > .env
```

Or export it before running:

```bash
export VITE_API_URL=http://your-api-url:8000
npm start
```

## API Endpoints Used

The frontend communicates with these backend endpoints:

### Templates
- `GET /templates` - Get all templates
- `GET /templates/{id}` - Get template by ID
- `POST /templates` - Create template
- `PUT /templates/{id}` - Update template
- `DELETE /templates/{id}` - Delete template
- `POST /templates/{id}/preview` - Preview template

### Message History
- `GET /history` - Query message history
- `GET /history/{id}` - Get history by ID

## Usage Guide

### Creating a Template

1. Click **"Create Template"** button in the header
2. Enter a unique template name (e.g., `welcome_email`)
3. Select channel type (Email or SMS)
4. For Email: Enter subject and content
5. For SMS: Enter content
6. Use Jinja2 syntax for variables: `{{variable_name}}`
7. Click **"Create Template"**

**Example Email Template:**
```
Name: welcome_email
Subject: Welcome {{name}}!
Content: <h1>Hello {{name}}</h1><p>Thanks for joining us!</p>
```

**Example SMS Template:**
```
Name: verification_sms
Content: Hi {{name}}! Your verification code is {{code}}.
```

### Editing a Template

1. Find the template in the list
2. Click the **"Edit"** button
3. Modify the content or subject (name and channel type cannot be changed)
4. Click **"Update Template"**

### Previewing a Template

1. Click the **"Preview"** button on a template card, or
2. Go to the **"Preview"** tab and select a template
3. Fill in values for all detected variables
4. Click **"Generate Preview"**
5. View the rendered result

### Viewing Message History

1. Click the **"History"** button on a template card, or
2. Go to the **"Message History"** tab
3. Use filters to narrow down results:
   - Filter by template
   - Filter by channel type (email/sms)
   - Filter by status (success/failed/partial)
4. Click on a message to expand and see full content

### Searching and Filtering

- Use the search box to find templates by name (searches as you type)
- Select a channel type filter (All, Email, SMS)
- Active filters are displayed as badges
- Click **"Clear"** to remove all filters
- Click refresh icon to reload templates

## Keyboard Shortcuts

- `Esc` - Close open modals
- `Ctrl/Cmd + F` - Focus search input (when available)

## Responsive Breakpoints

The UI adapts to different screen sizes:

- **Mobile (< 768px)**: Single column layout, stacked components
- **Tablet (768px - 1024px)**: 2-column grid for templates
- **Desktop (> 1024px)**: 3-column grid, side panels for details

## Troubleshooting

### Connection Error

**Error:** "Network error. Please check your connection and ensure the backend is running."

**Solution:**
1. Check if backend is running: `curl http://localhost:8000/health`
2. Start the backend: `python3 run_server.py`
3. Check for port conflicts: `lsof -i :8000`

### Template Not Found (404)

**Error:** "Template not found"

**Solution:**
- The template may have been deleted
- Click the refresh button to reload the template list

### Preview Failed

**Error:** "Template rendering error"

**Possible causes:**
1. Missing variable values - fill in all detected variables
2. Invalid Jinja2 syntax - check template content
3. Backend validation error - check the error message details

### Blank Page

**Issue:** Application shows a blank page

**Solution:**
1. Open browser console (F12) to see errors
2. Check if Node.js version is 18+: `node --version`
3. Reinstall dependencies: `rm -rf node_modules && npm install`
4. Clear browser cache and reload

## Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Technologies Used

- **React 18** - Component-based UI library
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - Promise-based HTTP client
- **React Syntax Highlighter** - Code syntax highlighting with Prism
- **React Toastify** - Toast notification system

## Development Tips

### Hot Reload

The development server supports hot module replacement (HMR). Changes to React components will update instantly without page reload.

### Debugging

1. Open browser DevTools (F12)
2. Check the Console tab for errors
3. Check the Network tab to see API calls
4. API requests are logged with `[API]` prefix

### Adding New Features

1. Components go in `src/components/`
2. API methods go in `src/services/api.js`
3. Global styles go in `src/index.css`
4. Use Tailwind utility classes for styling

## Performance

- **Debounced search** - Search input waits 300ms before filtering
- **Lazy rendering** - Content preview is collapsed by default
- **Optimized builds** - Vite creates optimized production bundles
- **Code splitting** - Syntax highlighter is loaded on demand

## Accessibility

- Semantic HTML elements
- ARIA labels for screen readers
- Keyboard navigation support
- Focus indicators on interactive elements
- High contrast color scheme

## License

This project is part of the Communications API exercise.

## Support

For issues or questions:
1. Check the backend logs: Backend console output
2. Check the frontend console: Browser DevTools (F12)
3. Verify all prerequisites are installed
4. Ensure the backend API is running

---

**Built with ❤️ for the LendBuzz Home Assignment**
