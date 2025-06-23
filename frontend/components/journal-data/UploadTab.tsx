"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  AlertCircle,
  CheckCircle2,
  FileSpreadsheet,
  Upload,
  Calendar,
  Trash2,
} from "lucide-react";

interface JournalDataUploadResponse {
  status: string;
  message: string;
  processed_count: number;
  failed_count: number;
  pinecone_index_name: string;
  details?: any;
  data_exists?: boolean;
  existing_count?: number;
}

interface UploadTabProps {
  selectedFiles: File[];
  setSelectedFiles: (files: File[]) => void;
  fiscalYear: number;
  setFiscalYear: (year: number) => void;
  fiscalMonth: number;
  setFiscalMonth: (month: number) => void;
  isUploading: boolean;
  uploadProgress: number;
  uploadResult: JournalDataUploadResponse | null;
  error: string | null;
  onUpload: () => void;
  onFileSelect: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onDragOver: (event: React.DragEvent) => void;
  onDrop: (event: React.DragEvent) => void;
  setError: (error: string | null) => void;
  fileInputRef?: React.RefObject<HTMLInputElement | null>;
}

export default function UploadTab({
  selectedFiles,
  setSelectedFiles,
  fiscalYear,
  setFiscalYear,
  fiscalMonth,
  setFiscalMonth,
  isUploading,
  uploadProgress,
  uploadResult,
  error,
  onUpload,
  onFileSelect,
  onDragOver,
  onDrop,
  setError,
  fileInputRef,
}: UploadTabProps) {
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Upload className="h-5 w-5" />
            <span>仕訳データ登録</span>
          </CardTitle>
          <CardDescription>
            会計システムからエクスポートした仕訳データ（CSV/Excel）をアップロードして、ベクトル化・保存します
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 会計期間設定 */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label
                htmlFor="fiscal-year"
                className="flex items-center space-x-1"
              >
                <Calendar className="h-4 w-4" />
                <span>会計年度</span>
              </Label>
              <Input
                id="fiscal-year"
                type="number"
                value={fiscalYear}
                onChange={(e) => setFiscalYear(parseInt(e.target.value))}
                min="2020"
                max="2030"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="fiscal-month">会計月</Label>
              <Input
                id="fiscal-month"
                type="number"
                value={fiscalMonth}
                onChange={(e) => setFiscalMonth(parseInt(e.target.value))}
                min="1"
                max="12"
              />
            </div>
          </div>

          {/* ファイルアップロード */}
          <div className="space-y-4">
            <Label>仕訳データファイル</Label>
            <div
              onDragOver={onDragOver}
              onDrop={onDrop}
              className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors"
            >
              <FileSpreadsheet className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 mb-4">
                ファイルをここにドラッグ&ドロップするか、クリックして選択
              </p>
              <input
                type="file"
                multiple
                accept=".xlsx,.xls,.csv"
                onChange={onFileSelect}
                className="hidden"
                id="file-input"
                ref={fileInputRef}
              />
              <label htmlFor="file-input">
                <Button variant="outline" asChild>
                  <span>ファイルを選択</span>
                </Button>
              </label>
            </div>

            {/* 選択されたファイル一覧 */}
            {selectedFiles.length > 0 && (
              <div className="space-y-2">
                <Label>選択されたファイル</Label>
                {selectedFiles.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border"
                  >
                    <div className="flex items-center space-x-3">
                      <FileSpreadsheet className="h-5 w-5 text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-800 text-sm">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSelectedFiles(
                          selectedFiles.filter((_, i) => i !== index)
                        );
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}

            {/* 進捗表示 */}
            {isUploading && (
              <div className="space-y-2">
                <Label>アップロード進捗</Label>
                <Progress value={uploadProgress} className="w-full" />
                <p className="text-sm text-gray-600 text-center">
                  {uploadProgress}% 完了
                </p>
              </div>
            )}

            {/* アップロードボタン */}
            <Button
              onClick={onUpload}
              disabled={selectedFiles.length === 0 || isUploading}
              className="w-full"
              size="lg"
            >
              {isUploading ? "登録中..." : "仕訳データを登録"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* エラー表示 */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* 成功表示 */}
      {uploadResult && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription>
            <div className="space-y-3">
              <div>
                <h3 className="font-medium text-green-800">登録完了</h3>
                <p className="text-green-700 mt-1">{uploadResult.message}</p>
              </div>
              <div className="bg-white p-4 rounded-lg border border-green-200">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">処理成功:</span>
                    <span className="ml-2">
                      {uploadResult.processed_count}件
                    </span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">処理失敗:</span>
                    <span className="ml-2">{uploadResult.failed_count}件</span>
                  </div>
                </div>
                <div className="mt-2 text-sm">
                  <span className="font-medium text-gray-700">
                    Pineconeインデックス:
                  </span>
                  <span className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                    {uploadResult.pinecone_index_name}
                  </span>
                </div>
                {uploadResult.failed_count > 0 && (
                  <div className="mt-4">
                    <h4 className="font-medium text-red-800 mb-2">
                      一部のデータの処理に失敗しました
                    </h4>
                    <p className="text-red-700 text-sm">
                      詳細はサーバーログを確認してください
                    </p>
                  </div>
                )}
              </div>
            </div>
          </AlertDescription>
        </Alert>
      )}
    </>
  );
}
