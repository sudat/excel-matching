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
  Database,
  TrendingUp,
  Calculator,
  Users,
  Calendar,
  RefreshCw,
} from "lucide-react";
import { useStats } from "@/hooks/journal-data";
import { formatCurrency, formatDate } from "@/lib/journal-data/formatters";

export default function StatsTab() {
  const { statsData, statsLoading, refreshStats } = useStats();

  if (statsLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>統計情報</span>
          </CardTitle>
          <CardDescription>登録データの統計情報と分析結果</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600">統計情報を読み込み中...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!statsData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>統計情報</span>
          </CardTitle>
          <CardDescription>登録データの統計情報と分析結果</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <p className="text-gray-600">統計データがありません</p>
            <Button onClick={refreshStats} className="mt-4">
              <RefreshCw className="h-4 w-4 mr-2" />
              データを更新
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const {
    summary,
    amount_stats,
    monthly_breakdown,
    category_breakdown,
    person_breakdown,
    date_range,
  } = statsData;

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Database className="h-5 w-5" />
              <span>統計情報</span>
              <Badge variant="secondary">{summary.total_entries}件</Badge>
            </div>
            <Button onClick={refreshStats} variant="outline" size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              更新
            </Button>
          </CardTitle>
          <CardDescription>
            登録データの統計情報と分析結果
            {date_range.from && date_range.to && (
              <span className="ml-2">
                ({formatDate(date_range.from)} 〜 {formatDate(date_range.to)})
              </span>
            )}
          </CardDescription>
        </CardHeader>
      </Card>

      {/* サマリー統計 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Database className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">総仕訳件数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.total_entries.toLocaleString()}件
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">総金額</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatCurrency(summary.total_amount)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Calculator className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">科目数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.unique_categories}科目
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Users className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">担当者数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {summary.unique_persons}名
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 金額統計 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Calculator className="h-5 w-5" />
            <span>金額統計</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">平均金額</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(amount_stats.average)}
              </p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">最大金額</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(amount_stats.max)}
              </p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">最小金額</p>
              <p className="text-lg font-semibold text-gray-900">
                {formatCurrency(amount_stats.min)}
              </p>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">件数</p>
              <p className="text-lg font-semibold text-gray-900">
                {amount_stats.count.toLocaleString()}件
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 月別推移と科目別集計 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 月別推移 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Calendar className="h-5 w-5" />
              <span>月別推移</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {monthly_breakdown.map((month) => (
                <div
                  key={month.period}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {month.year}年{month.month}月
                    </p>
                    <p className="text-sm text-gray-600">{month.count}件</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {formatCurrency(month.total_amount)}
                    </p>
                  </div>
                </div>
              ))}
              {monthly_breakdown.length === 0 && (
                <p className="text-center text-gray-600 py-8">
                  月別データがありません
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 科目別集計 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>科目別集計（上位10件）</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {category_breakdown.map((category, index) => (
                <div
                  key={category.category}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span className="flex items-center justify-center w-6 h-6 bg-blue-600 text-white text-xs font-bold rounded-full">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">
                        {category.category}
                      </p>
                      <p className="text-sm text-gray-600">
                        {category.count}件
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">
                      {formatCurrency(category.total_amount)}
                    </p>
                  </div>
                </div>
              ))}
              {category_breakdown.length === 0 && (
                <p className="text-center text-gray-600 py-8">
                  科目データがありません
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 担当者別集計 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Users className="h-5 w-5" />
            <span>担当者別集計（上位10件）</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {person_breakdown.map((person, index) => (
              <div
                key={person.person}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <span className="flex items-center justify-center w-6 h-6 bg-green-600 text-white text-xs font-bold rounded-full">
                    {index + 1}
                  </span>
                  <div>
                    <p className="font-medium text-gray-900">{person.person}</p>
                    <p className="text-sm text-gray-600">{person.count}件</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-gray-900">
                    {formatCurrency(person.total_amount)}
                  </p>
                </div>
              </div>
            ))}
            {person_breakdown.length === 0 && (
              <p className="text-center text-gray-600 py-8 col-span-2">
                担当者データがありません
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
