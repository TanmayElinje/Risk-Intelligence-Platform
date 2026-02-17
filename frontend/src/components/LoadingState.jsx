// frontend/src/components/LoadingState.jsx
import React from 'react';
import { Loader2, AlertCircle, RefreshCw } from 'lucide-react';

export const LoadingSpinner = ({ size = 'md', text = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <Loader2 className={`${sizes[size]} text-blue-600 animate-spin`} />
      {text && <p className="mt-4 text-gray-600 text-sm">{text}</p>}
    </div>
  );
};

export const ErrorState = ({ 
  title = 'Something went wrong', 
  message = 'We encountered an error loading this content.',
  onRetry 
}) => (
  <div className="flex flex-col items-center justify-center p-8 text-center">
    <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
      <AlertCircle className="w-8 h-8 text-red-600" />
    </div>
    <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 mb-6 max-w-md">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <RefreshCw className="w-4 h-4" />
        Try Again
      </button>
    )}
  </div>
);

export const EmptyState = ({ 
  title = 'No data available', 
  message = 'There is no data to display at the moment.',
  action,
  actionLabel = 'Refresh'
}) => (
  <div className="flex flex-col items-center justify-center p-12 text-center">
    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mb-4">
      <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
      </svg>
    </div>
    <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
    <p className="text-gray-600 mb-6 max-w-md">{message}</p>
    {action && (
      <button
        onClick={action}
        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        {actionLabel}
      </button>
    )}
  </div>
);

// Composite component for handling all states
export const LoadingState = ({ 
  isLoading, 
  isError, 
  isEmpty, 
  error,
  onRetry,
  loadingText,
  errorTitle,
  errorMessage,
  emptyTitle,
  emptyMessage,
  children 
}) => {
  if (isLoading) {
    return <LoadingSpinner text={loadingText} />;
  }

  if (isError) {
    return (
      <ErrorState
        title={errorTitle}
        message={errorMessage || error?.message}
        onRetry={onRetry}
      />
    );
  }

  if (isEmpty) {
    return (
      <EmptyState
        title={emptyTitle}
        message={emptyMessage}
        action={onRetry}
        actionLabel="Refresh"
      />
    );
  }

  return children;
};

export default LoadingState;