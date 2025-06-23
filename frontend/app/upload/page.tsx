"use client";

import AppLayout from "@/components/layout/AppLayout";
import { useState } from "react";
import FileUploader from "@/components/upload/FileUploader";
import { ErrorDisplay, UploadResult } from "@/components/upload";
import {
  API_BASE_URL,
  type UploadResponse,
  type SheetInfo,
  type ExcelSheetsData,
} from "@/lib/upload";

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [excelSheets, setExcelSheets] = useState<ExcelSheetsData | null>(null);

  const handleUpload = async (
    title: string,
    description: string,
    files: File[]
  ) => {
    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const formData = new FormData();
      formData.append("title", title);
      if (description) {
        formData.append("description", description);
      }

      files.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch(`${API_BASE_URL}/upload/business-request`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "アップロードに失敗しました");
      }

      const result: UploadResponse = await response.json();
      setUploadResult(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "アップロード中にエラーが発生しました"
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleExcelSheetsReceived = (
    sessionId: string,
    filename: string,
    sheets: SheetInfo[]
  ) => {
    console.log("Excel sheets received:", { sessionId, filename, sheets });
    setExcelSheets({ sessionId, filename, sheets });
  };

  const handleSheetSelected = (sessionId: string, sheetName: string) => {
    console.log("Sheet selected:", { sessionId, sheetName });
    // TODO: ここで選択されたシートに対する次の処理を実装
    setError(null);
    // 一時的に成功メッセージを表示
    setUploadResult({
      status: "success",
      message: `シート「${sheetName}」が選択されました`,
      business_request_id: sessionId,
      uploaded_files: [
        {
          file_id: sessionId,
          filename: excelSheets?.filename || "Unknown",
          file_size: 0,
          file_type: "excel",
          storage_path: "",
        },
      ],
      total_files: 1,
    });
  };

  return (
    <AppLayout
      title="Excelファイルアップロード"
      subtitle="データ分析・照合処理"
    >
      {/* アップロードセクション */}
      <section className="mb-16">
        <FileUploader
          onUpload={handleUpload}
          onExcelSheetsReceived={handleExcelSheetsReceived}
          onSheetSelected={handleSheetSelected}
          isUploading={isUploading}
          apiBaseUrl={API_BASE_URL}
        />

        {/* エラー表示 */}
        {error && <ErrorDisplay error={error} />}

        {/* アップロード成功表示 */}
        {uploadResult && <UploadResult uploadResult={uploadResult} />}
      </section>
    </AppLayout>
  );
}
