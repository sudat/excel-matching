"use client";

import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileSpreadsheet, Upload, Database, History } from "lucide-react";

// コンポーネントのインポート
import UploadTab from "@/components/journal-data/UploadTab";
import DataListTab from "@/components/journal-data/DataListTab";
import HistoryTab from "@/components/journal-data/HistoryTab";
import StatsTab from "@/components/journal-data/StatsTab";
import OverwriteDialog from "@/components/journal-data/OverwriteDialog";

// 状態管理のインポート
import { JournalDataProvider } from "@/lib/journal-data/store";

// カスタムフックのインポート
import {
  useFileUpload,
  useJournalDataList,
  useOperationHistory,
  useTabManagement,
} from "@/hooks/journal-data";

// ユーティリティのインポート
import {
  formatCurrency,
  formatDate,
  formatDateTime,
  getActionBadgeColor,
  getActionDisplayName,
} from "@/lib/journal-data/formatters";

import AppLayout from "@/components/layout/AppLayout";

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
    uploadFiles,
    handleDragOver,
    handleDrop,
    handleOverwriteConfirm,
    handleOverwriteCancel,
    fileInputRef,
  } = useFileUpload();

  const {
    journalData,
    totalCount,
    isLoading,
    searchTerm,
    dateFilter,
    error: dataListError,
    loadJournalData,
    handleSearch,
    handleDateFilter,
    handleDelete,
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
  const handleFileInputSelect = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const files = Array.from(event.target.files || []);
    handleFileSelect(files);
  };

  return (
    <AppLayout title="仕訳データ管理" subtitle="Journal Data Management">
      <Tabs
        value={activeTab}
        onValueChange={handleTabChange}
        className="w-full"
      >
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
            fileInputRef={fileInputRef}
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

      {/* 上書き確認ダイアログ */}
      <OverwriteDialog
        isOpen={showOverwriteDialog}
        fiscalYear={fiscalYear}
        fiscalMonth={fiscalMonth}
        onConfirm={handleOverwriteConfirm}
        onCancel={handleOverwriteCancel}
      />
    </AppLayout>
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
