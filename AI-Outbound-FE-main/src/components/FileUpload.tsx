import React, { useCallback, useState } from 'react';
import { FileUploadProps } from '../types/upload';

const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onNewUpload,
  acceptedFileTypes = '.csv',
  maxFileSize = 5 // 5MB default
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateFile = (file: File): boolean => {
    if (!file.name.endsWith('.csv')) {
      setError('Please upload a CSV file');
      return false;
    }

    if (file.size > maxFileSize * 1024 * 1024) {
      setError(`File size should be less than ${maxFileSize}MB`);
      return false;
    }

    setError(null);
    return true;
  };

  const handleFileSelect = useCallback((file: File) => {
    if (validateFile(file)) {
      onFileSelect(file);
    }
  }, [onFileSelect, maxFileSize]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
    // Reset the input value to allow selecting the same file again
    e.target.value = '';
  }, [handleFileSelect]);

  const handleClick = useCallback(() => {
    if (onNewUpload) {
      onNewUpload();
    }
  }, [onNewUpload]);

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          type="file"
          accept={acceptedFileTypes}
          className="hidden"
          id="file-upload"
          onChange={handleFileInput}
        />
        <label htmlFor="file-upload" className="cursor-pointer">
          <div className="flex flex-col items-center">
            <svg
              className="w-12 h-12 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="text-lg text-gray-600">
              Drag and drop your CSV file here, or{' '}
              <span className="text-blue-500 hover:text-blue-700">browse</span>
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Maximum file size: {maxFileSize}MB
            </p>
          </div>
        </label>
      </div>
      {error && (
        <p className="text-red-500 text-sm mt-2">{error}</p>
      )}
    </div>
  );
};

export default FileUpload; 