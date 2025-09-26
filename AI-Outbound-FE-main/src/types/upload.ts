export interface UploadedFile {
  name: string;
  size: number;
  type: string;
  lastModified: number;
}

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onNewUpload?: () => void;
  acceptedFileTypes?: string;
  maxFileSize?: number; // in MB
} 