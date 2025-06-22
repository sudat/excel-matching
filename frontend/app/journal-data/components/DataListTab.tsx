"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileSpreadsheet,
  Search,
  Trash2,
} from "lucide-react";

interface JournalEntry {
  id: string;
  entry_date: string;
  amount: number;
  person: string;
  category: string;
  description: string;
  account_code?: string;
  department?: string;
  sub_account?: string;
  partner?: string;
  detail_description?: string;
  source_file: string;
  registered_at: string;
}

interface DataListTabProps {
  journalData: JournalEntry[];
  totalCount: number;
  isLoading: boolean;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  dateFilter: string;
  setDateFilter: (filter: string) => void;
  onLoadData: () => void;
  onDelete: (entryId: string) => void;
  formatCurrency: (amount: number) => string;
  formatDate: (dateString: string) => string;
}

export default function DataListTab({
  journalData,
  totalCount,
  isLoading,
  searchTerm,
  setSearchTerm,
  dateFilter,
  setDateFilter,
  onLoadData,
  onDelete,
  formatCurrency,
  formatDate,
}: DataListTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <FileSpreadsheet className="h-5 w-5" />
            <span>登録済み仕訳データ</span>
            <Badge variant="secondary">{totalCount}件</Badge>
          </div>
          <Button onClick={onLoadData} disabled={isLoading}>
            <Search className="h-4 w-4 mr-2" />
            更新
          </Button>
        </CardTitle>
        <CardDescription>
          登録済みの仕訳データを検索・管理できます
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 検索・フィルター */}
        <div className="flex space-x-4">
          <div className="flex-1">
            <Input
              placeholder="キーワード検索（担当者、摘要など）"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="w-48">
            <Input
              type="month"
              placeholder="年月フィルター"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
            />
          </div>
        </div>

        {/* データテーブル */}
        {isLoading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">データを読み込み中...</p>
          </div>
        ) : journalData.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">データがありません</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-gray-200">
              <thead>
                <tr className="bg-gray-50">
                  <th className="border border-gray-200 px-4 py-2 text-left">日付</th>
                  <th className="border border-gray-200 px-4 py-2 text-left">金額</th>
                  <th className="border border-gray-200 px-4 py-2 text-left">担当者</th>
                  <th className="border border-gray-200 px-4 py-2 text-left">科目</th>
                  <th className="border border-gray-200 px-4 py-2 text-left">摘要</th>
                  <th className="border border-gray-200 px-4 py-2 text-left">元ファイル</th>
                  <th className="border border-gray-200 px-4 py-2 text-center">操作</th>
                </tr>
              </thead>
              <tbody>
                {journalData.map((entry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="border border-gray-200 px-4 py-2">
                      {formatDate(entry.entry_date)}
                    </td>
                    <td className="border border-gray-200 px-4 py-2 text-right">
                      {formatCurrency(entry.amount)}
                    </td>
                    <td className="border border-gray-200 px-4 py-2">
                      {entry.person}
                    </td>
                    <td className="border border-gray-200 px-4 py-2">
                      {entry.category}
                    </td>
                    <td className="border border-gray-200 px-4 py-2 max-w-xs truncate">
                      {entry.description}
                    </td>
                    <td className="border border-gray-200 px-4 py-2 text-sm text-gray-600">
                      {entry.source_file}
                    </td>
                    <td className="border border-gray-200 px-4 py-2 text-center">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(entry.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}