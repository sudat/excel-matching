"use client";

import React from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  FileSpreadsheet,
  Upload,
  Database,
  History,
  ArrowLeft,
} from "lucide-react";
import Link from "next/link";

// コンポーネントのインポート
import UploadTab from "./components/UploadTab";
import DataListTab from "./components/DataListTab";
import HistoryTab from "./components/HistoryTab";
import StatsTab from "./components/StatsTab";
import OverwriteDialog from "./components/OverwriteDialog";

// 状態管理のインポート
import { JournalDataProvider } from "./store";

// カスタムフックのインポート
import {
  useFileUpload,
  useJournalDataList,
  useOperationHistory,
  useTabManagement,
} from "./hooks";

// ユーティリティのインポート
import {
  formatCurrency,
  formatDate,
  formatDateTime,
  getActionBadgeColor,
  getActionDisplayName,
} from "./utils/formatters";

// メインコンポーネント（カスタムフック使用）
function JournalDataPageContent() {
  // カスタムフックを使用してビジネスロジックを分離
  const {
    selectedFiles,
    fiscalYear,
    fiscalMonth,
    isUploading,
    uploadProgress,
    uploadResult,
    showOverwriteDialog,
    error: uploadError,
    handleFileSelect,
    handleDragOver,
    handleDrop,
    uploadFiles,
    handleOverwriteConfirm,
    handleOverwriteCancel,
  } = useFileUpload();

  const {
    journalData,
    totalCount,
    isLoading,
    searchTerm,
    dateFilter,
    error: dataListError,
    loadJournalData,
    handleDelete,
    handleSearch,
    handleDateFilter,
  } = useJournalDataList();

  const {
    historyData,
    historyLoading,
    historyTotalCount,
    error: historyError,
    refreshHistory,
  } = useOperationHistory();

  const {
    activeTab,
    handleTabChange,
    handleFiscalYearChange,
    handleFiscalMonthChange,
  } = useTabManagement();

  // エラーの統合（優先順位: アップロード > データ一覧 > 履歴）
  const error = uploadError || dataListError || historyError;

  // ファイル選択ハンドラー（input要素用）
  const handleFileInputSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    handleFileSelect(files);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* ヘッダー */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="w-full max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Link href="/">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  戻る
                </Button>
              </Link>
              <div className="flex items-center space-x-3">
                <div className="h-10 w-10 bg-gradient-to-br from-green-600 to-blue-600 rounded-lg flex items-center justify-center">
                  <Database className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    仕訳データ管理
                  </h1>
                  <p className="text-sm text-gray-600">
                    Journal Data Management
                  </p>
                </div>
              </div>
            </div>
            <Badge variant="secondary">事前準備フロー</Badge>
          </div>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-4 py-8">
        <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>データ登録</span>
            </TabsTrigger>
            <TabsTrigger value="list" className="flex items-center space-x-2">
              <FileSpreadsheet className="h-4 w-4" />
              <span>データ一覧</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center space-x-2">
              <History className="h-4 w-4" />
              <span>操作履歴</span>
            </TabsTrigger>
            <TabsTrigger value="stats" className="flex items-center space-x-2">
              <Database className="h-4 w-4" />
              <span>統計情報</span>
            </TabsTrigger>
          </TabsList>

          {/* データ登録タブ */}
          <TabsContent value="upload" className="space-y-6">
            <UploadTab
              selectedFiles={selectedFiles}
              setSelectedFiles={handleFileSelect}
              fiscalYear={fiscalYear}
              setFiscalYear={handleFiscalYearChange}
              fiscalMonth={fiscalMonth}
              setFiscalMonth={handleFiscalMonthChange}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
              uploadResult={uploadResult}
              error={error}
              onUpload={uploadFiles}
              onFileSelect={handleFileInputSelect}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              setError={() => {}} // エラーはカスタムフック内で管理
            />
          </TabsContent>

          {/* データ一覧タブ */}
          <TabsContent value="list" className="space-y-6">
            <DataListTab
              journalData={journalData}
              totalCount={totalCount}
              isLoading={isLoading}
              searchTerm={searchTerm}
              setSearchTerm={handleSearch}
              dateFilter={dateFilter}
              setDateFilter={handleDateFilter}
              onLoadData={loadJournalData}
              onDelete={handleDelete}
              formatCurrency={formatCurrency}
              formatDate={formatDate}
            />
          </TabsContent>

          {/* 操作履歴タブ */}
          <TabsContent value="history" className="space-y-6">
            <HistoryTab
              historyData={historyData}
              historyLoading={historyLoading}
              historyTotalCount={historyTotalCount}
              onLoadHistory={refreshHistory}
              formatDateTime={formatDateTime}
              getActionBadgeColor={getActionBadgeColor}
              getActionDisplayName={getActionDisplayName}
            />
          </TabsContent>

          {/* 統計情報タブ */}
          <TabsContent value="stats" className="space-y-6">
            <StatsTab />
          </TabsContent>
        </Tabs>
      </main>

      {/* 上書き確認ダイアログ */}
      <OverwriteDialog
        isOpen={showOverwriteDialog}
        fiscalYear={fiscalYear}
        fiscalMonth={fiscalMonth}
        onConfirm={handleOverwriteConfirm}
        onCancel={handleOverwriteCancel}
      />
    </div>
  );
}

// Providerでラップしたメインコンポーネント
export default function JournalDataPage() {
  return (
    <JournalDataProvider>
      <JournalDataPageContent />
    </JournalDataProvider>
  );
}