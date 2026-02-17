// frontend/src/components/SkeletonLoader.jsx
import React from 'react';

// Base skeleton component
export const Skeleton = ({ className = '', width = 'w-full', height = 'h-4' }) => (
  <div className={`${width} ${height} ${className} bg-gray-200 rounded animate-pulse`} />
);

// Table skeleton
export const TableSkeleton = ({ rows = 5, columns = 4 }) => (
  <div className="bg-white rounded-lg shadow overflow-hidden">
    <div className="p-6 border-b">
      <Skeleton width="w-48" height="h-6" />
      <Skeleton width="w-64" height="h-4" className="mt-2" />
    </div>
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-50">
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="px-6 py-3">
                <Skeleton width="w-24" height="h-4" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {Array.from({ length: rows }).map((_, rowIndex) => (
            <tr key={rowIndex}>
              {Array.from({ length: columns }).map((_, colIndex) => (
                <td key={colIndex} className="px-6 py-4">
                  <Skeleton width="w-full" height="h-4" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

// Card skeleton
export const CardSkeleton = () => (
  <div className="bg-white rounded-lg shadow p-6">
    <Skeleton width="w-32" height="h-6" className="mb-4" />
    <div className="space-y-3">
      <Skeleton width="w-full" height="h-4" />
      <Skeleton width="w-5/6" height="h-4" />
      <Skeleton width="w-4/6" height="h-4" />
    </div>
  </div>
);

// Stat card skeleton
export const StatCardSkeleton = () => (
  <div className="bg-gray-50 rounded-lg p-6">
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <Skeleton width="w-24" height="h-4" className="mb-3" />
        <Skeleton width="w-20" height="h-10" />
      </div>
      <div className="w-12 h-12 bg-gray-300 rounded-full animate-pulse" />
    </div>
  </div>
);

// Grid skeleton
export const GridSkeleton = ({ items = 4, CardComponent = CardSkeleton }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    {Array.from({ length: items }).map((_, i) => (
      <CardComponent key={i} />
    ))}
  </div>
);

// Chart skeleton
export const ChartSkeleton = ({ title }) => (
  <div className="bg-white rounded-lg shadow p-6">
    <Skeleton width="w-48" height="h-6" className="mb-4" />
    <div className="h-64 bg-gray-100 rounded flex items-end justify-around p-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="bg-gray-300 rounded-t animate-pulse"
          style={{
            width: '10%',
            height: `${Math.random() * 80 + 20}%`,
            animationDelay: `${i * 0.1}s`
          }}
        />
      ))}
    </div>
  </div>
);

// Shimmer effect wrapper
export const ShimmerWrapper = ({ children, isLoading }) => {
  if (!isLoading) return children;

  return (
    <div className="relative overflow-hidden">
      {children}
      <div className="absolute inset-0 shimmer" />
      <style>{`
        .shimmer {
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(255, 255, 255, 0.6) 50%,
            transparent 100%
          );
          animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
};