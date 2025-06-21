'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface SheetInfo {
  name: string
  row_count: number
  col_count: number
  has_data: boolean
  data_range: string | null
  data_density: number
  estimated_data_cells: number
}

interface SheetSelectorProps {
  filename: string
  sheets: SheetInfo[]
  sessionId: string
  onSelectSheet: (sheetName: string) => void
  onBack?: () => void
  isLoading?: boolean
}

export function SheetSelector({ 
  filename, 
  sheets, 
  sessionId, 
  onSelectSheet, 
  onBack,
  isLoading = false 
}: SheetSelectorProps) {
  // データがあるシートを優先してソート
  const sortedSheets = [...sheets].sort((a, b) => {
    if (a.has_data && !b.has_data) return -1
    if (!a.has_data && b.has_data) return 1
    return b.estimated_data_cells - a.estimated_data_cells
  })

  const formatDataInfo = (sheet: SheetInfo) => {
    if (!sheet.has_data) {
      return 'データなし'
    }
    
    const density = Math.round(sheet.data_density * 100)
    return `${sheet.row_count}行 × ${sheet.col_count}列 (データ密度: ${density}%)`
  }

  const getSheetStatus = (sheet: SheetInfo) => {
    if (!sheet.has_data) {
      return { variant: 'secondary' as const, text: '空' }
    }
    if (sheet.data_density >= 0.1) {
      return { variant: 'default' as const, text: '推奨' }
    }
    return { variant: 'outline' as const, text: 'データ少' }
  }

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">シート選択</h2>
        <p className="text-gray-600">
          📊 <span className="font-medium">{filename}</span> - どのシートを解析しますか？
        </p>
        <p className="text-sm text-gray-500 mt-1">
          セッションID: {sessionId}
        </p>
      </div>

      <div className="space-y-3 mb-6">
        {sortedSheets.map((sheet, index) => {
          const status = getSheetStatus(sheet)
          
          return (
            <Card 
              key={sheet.name} 
              className={`transition-all hover:shadow-md ${
                !sheet.has_data ? 'opacity-60' : 'cursor-pointer hover:bg-gray-50'
              }`}
            >
              <CardContent className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-medium text-xs flex-shrink-0">
                      {index + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-base truncate">{sheet.name}</h3>
                        <Badge variant={status.variant} className="text-xs flex-shrink-0">{status.text}</Badge>
                      </div>
                      <div className="text-sm text-gray-600 mb-1">
                        {formatDataInfo(sheet)}
                      </div>
                      <div className="text-xs text-gray-500">
                        {sheet.data_range ? (
                          <>範囲: {sheet.data_range} • データセル: {sheet.estimated_data_cells}個</>
                        ) : (
                          '利用可能なデータがありません'
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => onSelectSheet(sheet.name)}
                    disabled={!sheet.has_data || isLoading}
                    variant={sheet.has_data ? "default" : "secondary"}
                    size="sm"
                    className="ml-3 flex-shrink-0"
                  >
                    {isLoading ? '処理中...' : sheet.has_data ? '選択' : '無効'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {sheets.length === 0 && (
        <Card className="text-center py-8">
          <CardContent>
            <p className="text-gray-500">
              このExcelファイルにはシートが見つかりませんでした。
            </p>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between items-center pt-4 border-t">
        <div className="text-sm text-gray-500">
          {sheets.filter(s => s.has_data).length}個のシートにデータが見つかりました
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