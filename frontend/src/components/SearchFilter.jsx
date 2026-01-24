import React, { useEffect, useRef } from 'react';

function SearchFilter({
  searchTerm,
  onSearchChange,
  channelFilter,
  onChannelFilterChange,
  onRefresh,
}) {
  const searchInputRef = useRef(null);
  const debounceTimerRef = useRef(null);

  // Debounced search
  const handleSearchChange = (e) => {
    const value = e.target.value;
    
    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // Set new timer
    debounceTimerRef.current = setTimeout(() => {
      onSearchChange(value);
    }, 300);
  };

  const handleClearFilters = () => {
    onSearchChange('');
    onChannelFilterChange('all');
    if (searchInputRef.current) {
      searchInputRef.current.value = '';
    }
  };

  const hasActiveFilters = searchTerm || channelFilter !== 'all';

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search Input */}
        <div className="flex-1">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg
                className="h-5 w-5 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            </div>
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search templates by name..."
              defaultValue={searchTerm}
              onChange={handleSearchChange}
              className="input pl-10"
            />
          </div>
        </div>

        {/* Channel Filter */}
        <div className="sm:w-48">
          <select
            value={channelFilter}
            onChange={(e) => onChannelFilterChange(e.target.value)}
            className="input"
          >
            <option value="all">All Channels</option>
            <option value="email">Email Only</option>
            <option value="sms">SMS Only</option>
          </select>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-2">
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="btn btn-secondary whitespace-nowrap"
              title="Clear all filters"
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
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
              Clear
            </button>
          )}
          <button
            onClick={onRefresh}
            className="btn btn-secondary"
            title="Refresh templates"
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-3 flex flex-wrap gap-2">
          {searchTerm && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-primary-100 text-primary-800">
              Search: {searchTerm}
              <button
                onClick={() => {
                  onSearchChange('');
                  if (searchInputRef.current) {
                    searchInputRef.current.value = '';
                  }
                }}
                className="ml-2 hover:text-primary-900"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </span>
          )}
          {channelFilter !== 'all' && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-success-100 text-success-800">
              Channel: {channelFilter.toUpperCase()}
              <button
                onClick={() => onChannelFilterChange('all')}
                className="ml-2 hover:text-success-900"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default SearchFilter;
