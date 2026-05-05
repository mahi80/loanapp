"use client";

import { useState, useRef, type DragEvent } from "react";
import { useSession } from "next-auth/react";
import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DocUploadWidgetProps {
  data: Record<string, unknown>;
  onSubmit?: (payload: Record<string, unknown>) => void;
}

export function DocUploadWidget({ data, onSubmit }: DocUploadWidgetProps) {
  const { data: session } = useSession();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploaded, setUploaded] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const docType = (data?.document_type as string) || "Document";

  const handleFile = (f: File) => {
    setFile(f);
    setUploaded(false);
    setError(null);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFile(dropped);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be under 10MB");
      setUploading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", docType);
      formData.append("application_id", "pending");

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const token = (session as any)?.backendToken || "";
      const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
        // Don't set Content-Type -- browser sets multipart boundary automatically
      });

      if (!res.ok) throw new Error("Upload failed");
      const resData = await res.json();

      setUploaded(true);
      onSubmit?.({
        tool: "upload_document",
        document_type: docType,
        file_name: file.name,
        document_id: resData.document_id,
      });
    } catch {
      setError("Upload failed. Please try again.");
    } finally {
      setUploading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-l-4 border-l-[#D4A853] shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-[#0F172A]">
            <FileText className="w-5 h-5 text-[#D4A853]" />
            Upload: {docType}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              "flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-8 cursor-pointer transition-colors",
              dragOver
                ? "border-[#D4A853] bg-[#D4A853]/5"
                : "border-slate-300 hover:border-[#D4A853]/50 hover:bg-slate-50"
            )}
          >
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png,.tiff,.tif,.bmp,.heif,.heic,.webp"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
            />

            {uploaded ? (
              <CheckCircle2 className="w-10 h-10 text-green-500" />
            ) : (
              <Upload className="w-10 h-10 text-[#D4A853]" />
            )}

            {file ? (
              <div className="text-center">
                <p className="text-sm font-medium text-slate-700">{file.name}</p>
                <p className="text-xs text-slate-400">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            ) : (
              <div className="text-center">
                <p className="text-sm text-slate-600">
                  Drag & drop your file here, or click to browse
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  PDF, JPG, PNG, TIFF, BMP, WebP up to 10MB
                </p>
              </div>
            )}
          </div>

          {error && (
            <p className="mt-2 text-sm text-red-600">{error}</p>
          )}

          {file && !uploaded && (
            <div className="mt-4 flex justify-end">
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="bg-[#0F172A] hover:bg-[#1E293B] text-white px-6"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Upload Document"
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
