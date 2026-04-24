"use client";

import { useState, useCallback } from "react";
import { UploadCloud, FileType, CheckCircle2, AlertCircle } from "lucide-react";
import axios from "axios";

export default function CSVUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const [stats, setStats] = useState<{added: number, skipped: number} | null>(null);

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
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith(".csv")) {
        setFile(droppedFile);
        setStatus("idle");
      } else {
        setStatus("error");
        setMessage("Please upload a valid CSV file.");
      }
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      if (selectedFile.name.endsWith(".csv")) {
        setFile(selectedFile);
        setStatus("idle");
      } else {
        setStatus("error");
        setMessage("Please upload a valid CSV file.");
      }
    }
  };

  const uploadFile = async () => {
    if (!file) return;

    setStatus("uploading");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:8000/api/upload-leads", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      setStatus("success");
      setStats({
        added: response.data.leads_added,
        skipped: response.data.leads_skipped_duplicates
      });
      setMessage("File uploaded and processed successfully!");
    } catch (err: any) {
      setStatus("error");
      setMessage(err.response?.data?.detail || "An error occurred during upload.");
    }
  };

  return (
    <div className="rounded-xl border bg-white p-8 shadow-sm">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Import Leads</h2>
        <p className="text-sm text-gray-500">Upload your Apify CSV exports here. Duplicates will be automatically skipped.</p>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 text-center transition-colors ${
          isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:bg-gray-50"
        }`}
      >
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          className="absolute inset-0 cursor-pointer opacity-0"
        />
        <UploadCloud className="mb-4 h-12 w-12 text-gray-400" />
        <h3 className="mb-1 text-base font-semibold text-gray-900">
          {file ? file.name : "Click or drag CSV to upload"}
        </h3>
        <p className="text-sm text-gray-500">
          {file ? "Ready to import" : "Apify exports, Apollo, etc."}
        </p>
      </div>

      {status === "error" && (
        <div className="mt-4 flex items-center rounded-md bg-red-50 p-4 text-red-700">
          <AlertCircle className="mr-3 h-5 w-5" />
          <p className="text-sm">{message}</p>
        </div>
      )}

      {status === "success" && (
        <div className="mt-4 flex flex-col rounded-md bg-green-50 p-4 text-green-700">
          <div className="flex items-center mb-2">
            <CheckCircle2 className="mr-3 h-5 w-5" />
            <p className="font-semibold">{message}</p>
          </div>
          {stats && (
            <ul className="ml-8 list-disc text-sm text-green-800">
              <li>{stats.added} new leads added</li>
              <li>{stats.skipped} duplicates skipped</li>
            </ul>
          )}
        </div>
      )}

      <div className="mt-6 flex justify-end">
        <button
          onClick={uploadFile}
          disabled={!file || status === "uploading"}
          className={`rounded-md px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition-all ${
            !file || status === "uploading"
              ? "cursor-not-allowed bg-blue-300"
              : "bg-blue-600 hover:bg-blue-500"
          }`}
        >
          {status === "uploading" ? "Processing..." : "Import Leads"}
        </button>
      </div>
    </div>
  );
}
