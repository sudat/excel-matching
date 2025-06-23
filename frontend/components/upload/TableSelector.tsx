'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ScrollArea } from '@/components/ui/scroll-area'

interface TableCandidate {
  table_id: string
  sheet_name: string
  range: {
    start_row: number
    end_row: number
    start_col: number
    end_col: number
    excel_range: string
  }
  header_row: number | null
  quality_score: number
  data_density: number
  dimensions: {
    row_count: number
    col_count: number
    estimated_records: number
  }
  headers: string[]
  sample_data: Array<Record<string, string>>
  metadata: {
    detection_method: string
    data_cells: number
    total_cells: number
  }
}

interface TableSelectorProps {
  filename: string
  sheetName: string
  tables: TableCandidate[]
  sessionId: string
  onSelectTable: (tableId: string) => void
  onBack?: () => void
  isLoading?: boolean
}

export function TableSelector({ 
  filename, 
  sheetName,
  tables, 
  sessionId, 
  onSelectTable, 
  onBack,
  isLoading = false 
}: TableSelectorProps) {
  // 品質スコアでソート（既にソート済みだが念のため）
  const sortedTables = [...tables].sort((a, b) => b.quality_score - a.quality_score)

  const getQualityStatus = (qualityScore: number) => {
    if (qualityScore >= 0.7) {
      return { variant: 'default' as const, text: '高品質', color: 'text-green-600' }
    } else if (qualityScore >= 0.5) {
      return { variant: 'secondary' as const, text: '中品質', color: 'text-yellow-600' }
    } else {
      return { variant: 'outline' as const, text: '低品質', color: 'text-gray-600' }
    }
  }

  const formatRange = (range: TableCandidate['range']) => {
    return `${range.excel_range} (${range.start_row}:${range.end_row}, ${range.start_col}:${range.end_col})`
  }

  const renderSampleTable = (table: TableCandidate) => {
    if (!table.sample_data || table.sample_data.length === 0) {
      return (
        <div className="text-sm text-gray-500 p-4 text-center">
          サンプルデータがありません
        </div>
      )
    }

    const headers = table.headers || Object.keys(table.sample_data[0] || {})
    
    return (
      <div className="mt-3">
        <p className="text-sm font-medium text-gray-700 mb-2">サンプルデータ（ヘッダー + 先頭3行）</p>
        <ScrollArea className="h-40 border rounded">
          <Table className="text-xs">
            <TableHeader>
              <TableRow>
                {headers.map((header, idx) => (
                  <TableHead key={idx} className="font-medium text-xs px-2 py-1">
                    {header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {table.sample_data.slice(0, 3).map((row, rowIdx) => (
                <TableRow key={rowIdx}>
                  {headers.map((header, colIdx) => (
                    <TableCell key={colIdx} className="px-2 py-1 text-xs">
                      {row[header] || ''}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </ScrollArea>
      </div>
    )
  }

  return (
    <div className="w-full max-w-6xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">表選択</h2>
        <p className="text-gray-600">
          📊 <span className="font-medium">{filename}</span> - シート「{sheetName}」
        </p>
        <p className="text-sm text-gray-500 mt-1">
          どの表を解析しますか？ • セッションID: {sessionId}
        </p>
      </div>

      <div className="space-y-4 mb-6">
        {sortedTables.map((table, index) => {
          const qualityStatus = getQualityStatus(table.quality_score)
          
          return (
            <Card 
              key={table.table_id} 
              className="transition-all hover:shadow-md"
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-medium text-sm flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">表 {table.table_id}</h3>
                        <Badge variant={qualityStatus.variant}>{qualityStatus.text}</Badge>
                        <span className={`text-sm font-medium ${qualityStatus.color}`}>
                          スコア: {(table.quality_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-700">サイズ:</span>
                          <p>{table.dimensions.row_count}行 × {table.dimensions.col_count}列</p>
                          <p className="text-gray-600">推定レコード数: {table.dimensions.estimated_records}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-700">データ密度:</span>
                          <p>{(table.data_density * 100).toFixed(1)}% ({table.metadata.data_cells}/{table.metadata.total_cells})</p>
                          <p className="text-gray-600">範囲: {formatRange(table.range)}</p>
                        </div>
                        
                        <div>
                          <span className="font-medium text-gray-700">ヘッダー:</span>
                          <p>{table.header_row ? `${table.header_row}行目` : 'なし'}</p>
                          <p className="text-gray-600">列数: {table.headers.length}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => onSelectTable(table.table_id)}
                    disabled={isLoading}
                    variant="default"
                    size="sm"
                    className="ml-4 flex-shrink-0"
                  >
                    {isLoading ? '処理中...' : '選択'}
                  </Button>
                </div>

                {/* サンプルテーブル */}
                {renderSampleTable(table)}
              </CardContent>
            </Card>
          )
        })}
      </div>

      {tables.length === 0 && (
        <Card className="text-center py-8">
          <CardContent>
            <p className="text-gray-500">
              このシートには表が見つかりませんでした。
            </p>
            <p className="text-sm text-gray-400 mt-2">
              最小3行2列の条件を満たす表がないか、データ密度が低すぎる可能性があります。
            </p>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between items-center pt-4 border-t">
        <div className="text-sm text-gray-500">
          {tables.length}個の表が検出されました
        </div>
        
        {onBack && (
          <Button variant="outline" onClick={onBack} disabled={isLoading}>
            戻る
          </Button>
        )}
      </div>
    </div>
  )
}