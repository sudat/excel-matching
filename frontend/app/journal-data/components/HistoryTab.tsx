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
import {
  History,
  Search,
} from "lucide-react";

interface HistoryItem {
  id: string;
  timestamp: string;
  action: string;
  user_id: string;
  details: any;
  result: string;
  description: string;
}

interface HistoryTabProps {
  historyData: HistoryItem[];
  historyLoading: boolean;
  historyTotalCount: number;
  onLoadHistory: () => void;
  formatDateTime: (dateString: string) => string;
  getActionBadgeColor: (action: string) => string;
  getActionDisplayName: (action: string) => string;
}

export default function HistoryTab({
  historyData,
  historyLoading,
  historyTotalCount,
  onLoadHistory,
  formatDateTime,
  getActionBadgeColor,
  getActionDisplayName,
}: HistoryTabProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <History className="h-5 w-5" />
            <span>操作履歴</span>
            <Badge variant="secondary">{historyTotalCount}件</Badge>
          </div>
          <Button onClick={onLoadHistory} disabled={historyLoading}>
            <Search className="h-4 w-4 mr-2" />
            更新
          </Button>
        </CardTitle>
        <CardDescription>
          仕訳データの登録・削除などの操作履歴を確認できます
        </CardDescription>
      </CardHeader>
      <CardContent>
        {historyLoading ? (
          <div className="text-center py-8">
            <p className="text-gray-600">履歴データを読み込み中...</p>
          </div>
        ) : historyData.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-600">操作履歴がありません</p>
          </div>
        ) : (
          <div className="space-y-4">
            {historyData.map((item, index) => (
              <div
                key={item.id || index}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionBadgeColor(
                          item.action
                        )}`}
                      >
                        {getActionDisplayName(item.action)}
                      </span>
                      <span className="text-sm text-gray-500">
                        {formatDateTime(item.timestamp)}
                      </span>
                      <span className="text-sm text-gray-500">
                        ユーザー: {item.user_id}
                      </span>
                    </div>
                    <p className="text-gray-900 font-medium mb-2">
                      {item.description}
                    </p>
                    {item.details && Object.keys(item.details).length > 0 && (
                      <div className="bg-gray-50 rounded-md p-3 mt-2">
                        <p className="text-sm font-medium text-gray-700 mb-1">詳細情報:</p>
                        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                          {item.details.fiscal_year && item.details.fiscal_month && (
                            <div>
                              <span className="font-medium">対象期間:</span>{" "}
                              {item.details.fiscal_year}年{item.details.fiscal_month}月
                            </div>
                          )}
                          {item.details.entry_count && (
                            <div>
                              <span className="font-medium">処理件数:</span>{" "}
                              {item.details.entry_count}件
                            </div>
                          )}
                          {item.details.source_files && (
                            <div className="col-span-2">
                              <span className="font-medium">ファイル:</span>{" "}
                              {Array.isArray(item.details.source_files)
                                ? item.details.source_files.join(", ")
                                : item.details.source_files}
                            </div>
                          )}
                          {item.details.uploaded_files && (
                            <div className="col-span-2">
                              <span className="font-medium">アップロードファイル:</span>{" "}
                              {Array.isArray(item.details.uploaded_files)
                                ? item.details.uploaded_files.join(", ")
                                : item.details.uploaded_files}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        item.result === "success"
                          ? "bg-green-100 text-green-800"
                          : item.result === "failed"
                          ? "bg-red-100 text-red-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {item.result === "success" ? "成功" : item.result === "failed" ? "失敗" : "不明"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}