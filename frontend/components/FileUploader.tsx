'use client'

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, File, X, AlertCircle, CheckCircle2, FileSpreadsheet } from 'lucide-react'
import { SheetSelector } from './SheetSelector'
import { TableSelector } from './TableSelector'

interface UploadedFile {
  file: File
  id: string
}

interface SheetInfo {
  name: string
  row_count: number
  col_count: number
  has_data: boolean
  data_range: string | null
  data_density: number
  estimated_data_cells: number
}

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

interface UploadState {
  step: 'upload' | 'select-sheet' | 'select-table' | 'processing' | 'complete'
  sessionId?: string
  filename?: string
  availableSheets?: SheetInfo[]
  selectedSheet?: string
  availableTables?: TableCandidate[]
  selectedTable?: string
}

interface FileUploaderProps {
  onUpload: (title: string, description: string, files: File[]) => Promise<void>
  onExcelSheetsReceived?: (sessionId: string, filename: string, sheets: SheetInfo[]) => void
  onSheetSelected?: (sessionId: string, sheetName: string) => void
  onTableSelected?: (sessionId: string, tableId: string) => void
  isUploading: boolean
  apiBaseUrl?: string
}

const FileUploader: React.FC<FileUploaderProps> = ({ 
  onUpload, 
  onExcelSheetsReceived,
  onSheetSelected,
  onTableSelected,
  isUploading,
  apiBaseUrl = 'http://localhost:8000'
}) => {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<UploadedFile[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<string[]>([])
  const [uploadState, setUploadState] = useState<UploadState>({ step: 'upload' })
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 許可されるファイルタイプ
  const allowedTypes = [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
    'application/vnd.ms-excel', // .xls
    'text/csv', // .csv
    'application/csv' // .csv
  ]

  // ファイルサイズ制限（10MB）
  const maxFileSize = 10 * 1024 * 1024

  const validateFile = (file: File): string | null => {
    // ファイルタイプチェック
    if (!allowedTypes.includes(file.type)) {
      const extension = file.name.split('.').pop()?.toLowerCase()
      if (!['xlsx', 'xls', 'csv'].includes(extension || '')) {
        return `サポートされていないファイル形式です: ${file.name}`
      }
    }

    // ファイルサイズチェック
    if (file.size > maxFileSize) {
      return `ファイルサイズが大きすぎます（最大10MB）: ${file.name}`
    }

    return null
  }

  const handleFiles = (files: FileList | null) => {
    if (!files) return

    const newFiles: UploadedFile[] = []
    const newErrors: string[] = []

    // 最大5ファイル制限
    if (selectedFiles.length + files.length > 5) {
      setErrors(['最大5ファイルまでアップロード可能です'])
      return
    }

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      
      // 既存ファイルとの重複チェック
      if (selectedFiles.some(sf => sf.file.name === file.name)) {
        newErrors.push(`既に選択されています: ${file.name}`)
        continue
      }

      // ファイル検証
      const error = validateFile(file)
      if (error) {
        newErrors.push(error)
        continue
      }

      newFiles.push({
        file,
        id: Math.random().toString(36).substring(2, 11)
      })
    }

    setErrors(newErrors)

    if (newFiles.length > 0) {
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
  }

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files)
    }
  }

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files)
    }
  }

  const removeFile = (id: string) => {
    setSelectedFiles(prev => prev.filter(file => file.id !== id))
  }

  const onButtonClick = () => {
    fileInputRef.current?.click()
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getFileIcon = () => {
    return <FileSpreadsheet className="h-5 w-5 text-green-600" />
  }

  const isExcelFile = (file: File): boolean => {
    const extension = file.name.split('.').pop()?.toLowerCase()
    return ['xlsx', 'xls'].includes(extension || '')
  }

  const handleExcelSheetsUpload = async (file: File) => {
    try {
      setUploadState({ step: 'processing' })
      
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${apiBaseUrl}/api/parse-excel-sheets`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.status === 'success') {
        setUploadState({
          step: 'select-sheet',
          sessionId: result.session_id,
          filename: result.data.filename,
          availableSheets: result.data.sheets
        })
        
        if (onExcelSheetsReceived) {
          onExcelSheetsReceived(result.session_id, result.data.filename, result.data.sheets)
        }
      } else {
        throw new Error(result.message || 'シート情報の取得に失敗しました')
      }
    } catch (error) {
      console.error('Excel sheets upload failed:', error)
      setErrors([error instanceof Error ? error.message : 'Excelファイルの処理に失敗しました'])
      setUploadState({ step: 'upload' })
    }
  }

  const handleSheetSelection = async (sheetName: string) => {
    if (!uploadState.sessionId) return
    
    try {
      setUploadState(prev => ({
        ...prev,
        step: 'processing'
      }))
      
      // 表検出APIを呼び出し
      const encodedSheetName = encodeURIComponent(sheetName)
      const response = await fetch(`${apiBaseUrl}/api/excel-sheet-tables/${uploadState.sessionId}/${encodedSheetName}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.status === 'success' && result.data.tables.length > 0) {
        // 複数の表が見つかった場合は表選択画面へ
        setUploadState({
          step: 'select-table',
          sessionId: uploadState.sessionId,
          filename: uploadState.filename,
          availableSheets: uploadState.availableSheets,
          selectedSheet: sheetName,
          availableTables: result.data.tables
        })
      } else if (result.data.tables.length === 0) {
        // 表が見つからない場合
        setErrors(['選択されたシートには表が見つかりませんでした。他のシートを試してください。'])
        setUploadState(prev => ({
          ...prev,
          step: 'select-sheet'
        }))
      } else {
        throw new Error(result.message || '表検出に失敗しました')
      }
      
      if (onSheetSelected) {
        onSheetSelected(uploadState.sessionId, sheetName)
      }
    } catch (error) {
      console.error('Table detection failed:', error)
      setErrors([error instanceof Error ? error.message : '表検出に失敗しました'])
      setUploadState(prev => ({
        ...prev,
        step: 'select-sheet'
      }))
    }
  }

  const handleTableSelection = async (tableId: string) => {
    if (!uploadState.sessionId) return
    
    try {
      setUploadState(prev => ({
        ...prev,
        step: 'processing'
      }))
      
      // 表選択APIを呼び出し
      const response = await fetch(`${apiBaseUrl}/api/select-table/${uploadState.sessionId}/${tableId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (result.status === 'success') {
        setUploadState(prev => ({
          ...prev,
          selectedTable: tableId,
          step: 'complete'
        }))
        
        if (onTableSelected) {
          onTableSelected(uploadState.sessionId, tableId)
        }
      } else {
        throw new Error(result.message || '表選択に失敗しました')
      }
    } catch (error) {
      console.error('Table selection failed:', error)
      setErrors([error instanceof Error ? error.message : '表選択に失敗しました'])
      setUploadState(prev => ({
        ...prev,
        step: 'select-table'
      }))
    }
  }

  const handleBackToSheetSelection = () => {
    setUploadState(prev => ({
      ...prev,
      step: 'select-sheet',
      availableTables: undefined
    }))
    setErrors([])
  }

  const handleBackToUpload = () => {
    setUploadState({ step: 'upload' })
    setSelectedFiles([])
    setErrors([])
  }

  const handleSubmit = async () => {
    if (!title.trim()) {
      setErrors(['業務依頼のタイトルを入力してください'])
      return
    }

    if (selectedFiles.length === 0) {
      setErrors(['少なくとも1つのファイルを選択してください'])
      return
    }

    const files = selectedFiles.map(sf => sf.file)
    
    // Excelファイルが含まれている場合の特別処理
    const excelFiles = files.filter(isExcelFile)
    if (excelFiles.length === 1 && files.length === 1) {
      // 単一のExcelファイルの場合はシート選択フローへ
      await handleExcelSheetsUpload(excelFiles[0])
      return
    }
    
    try {
      await onUpload(title, description, files)
      // アップロード成功後、フォームをリセット
      setTitle('')
      setDescription('')
      setSelectedFiles([])
      setErrors([])
      setUploadState({ step: 'upload' })
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  // シート選択画面を表示
  if (uploadState.step === 'select-sheet' && uploadState.availableSheets && uploadState.sessionId && uploadState.filename) {
    return (
      <SheetSelector
        filename={uploadState.filename}
        sheets={uploadState.availableSheets}
        sessionId={uploadState.sessionId}
        onSelectSheet={handleSheetSelection}
        onBack={handleBackToUpload}
        isLoading={isUploading}
      />
    )
  }

  // 表選択画面を表示
  if (uploadState.step === 'select-table' && uploadState.availableTables && uploadState.sessionId && uploadState.filename && uploadState.selectedSheet) {
    return (
      <TableSelector
        filename={uploadState.filename}
        sheetName={uploadState.selectedSheet}
        tables={uploadState.availableTables}
        sessionId={uploadState.sessionId}
        onSelectTable={handleTableSelection}
        onBack={handleBackToSheetSelection}
        isLoading={isUploading}
      />
    )
  }

  // 処理中画面
  if (uploadState.step === 'processing') {
    const getProcessingMessage = () => {
      if (uploadState.selectedSheet && !uploadState.availableTables) {
        return {
          title: 'シート内の表を検出中...',
          description: `シート「${uploadState.selectedSheet}」から表を検出しています`
        }
      } else if (uploadState.availableTables) {
        return {
          title: '表データを取得中...',
          description: '選択された表のデータを処理しています'
        }
      } else {
        return {
          title: 'Excelファイルを解析中...',
          description: 'シート情報を取得しています'
        }
      }
    }

    const message = getProcessingMessage()

    return (
      <div className="w-full max-w-4xl mx-auto">
        <Card className="border-2 shadow-lg">
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <h3 className="text-lg font-medium">{message.title}</h3>
              <p className="text-muted-foreground">{message.description}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // 完了画面
  if (uploadState.step === 'complete') {
    return (
      <div className="w-full max-w-4xl mx-auto">
        <Card className="border-2 shadow-lg">
          <CardContent className="p-8 text-center">
            <div className="space-y-4">
              <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto" />
              <h3 className="text-lg font-medium">表選択完了</h3>
              <div className="text-muted-foreground space-y-1">
                <p>ファイル: <span className="font-medium">{uploadState.filename}</span></p>
                <p>シート: <span className="font-medium">{uploadState.selectedSheet}</span></p>
                {uploadState.selectedTable && (
                  <p>表: <span className="font-medium">{uploadState.selectedTable}</span></p>
                )}
              </div>
              <p className="text-sm text-gray-600">
                選択された表のデータが正常に取得されました
              </p>
              <Button onClick={handleBackToUpload} variant="outline">
                新しいファイルをアップロード
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <Card className="border-2 shadow-lg">
        <CardHeader className="pb-4">
          <CardTitle className="text-2xl font-bold flex items-center gap-2">
            <Upload className="h-6 w-6 text-primary" />
            Excel/CSVファイルアップロード
          </CardTitle>
          <CardDescription className="text-base">
            業務依頼を作成し、分析対象のファイルをアップロードしてください
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 業務依頼情報入力 */}
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="title" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                業務依頼タイトル <span className="text-destructive">*</span>
              </label>
              <Input
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="例: 顧客データマッチング分析"
                disabled={isUploading}
                className="h-11"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                説明（任意）
              </label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="業務依頼の詳細説明を入力してください..."
                disabled={isUploading}
                rows={3}
                className="resize-none"
              />
            </div>
          </div>

          {/* エラー表示 */}
          {errors.length > 0 && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                <ul className="list-disc list-inside space-y-1">
                  {errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}

          {/* ファイルアップロード領域 */}
          <Card className={`border-2 border-dashed transition-all duration-200 ${
            dragActive
              ? 'border-primary bg-primary/5 shadow-md'
              : 'border-muted-foreground/25 hover:border-muted-foreground/50'
          } ${isUploading ? 'pointer-events-none opacity-50' : 'cursor-pointer'}`}>
            <CardContent
              className="p-8 text-center"
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={onButtonClick}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".xlsx,.xls,.csv"
                onChange={handleChange}
                className="hidden"
                disabled={isUploading}
              />

              <div className="space-y-4">
                <div className={`transition-all duration-200 ${
                  dragActive ? 'text-primary scale-110' : 'text-muted-foreground'
                }`}>
                  <Upload className="h-12 w-12 mx-auto" />
                </div>
                
                <div className="space-y-2">
                  <p className="text-lg font-medium">
                    ファイルをドラッグ&ドロップ
                  </p>
                  <p className="text-muted-foreground">
                    または
                  </p>
                  <Button variant="outline" size="lg" disabled={isUploading}>
                    <File className="h-4 w-4 mr-2" />
                    ファイルを選択
                  </Button>
                </div>

                <div className="text-sm text-muted-foreground space-y-1">
                  <p>サポート形式: .xlsx, .xls, .csv</p>
                  <p>最大ファイルサイズ: 10MB</p>
                  <p>最大ファイル数: 5個</p>
                </div>
              </div>

              {dragActive && (
                <div className="absolute inset-0 bg-primary/10 rounded-lg flex items-center justify-center backdrop-blur-sm">
                  <div className="text-primary font-medium text-lg">
                    ファイルをドロップしてください
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 選択されたファイル一覧 */}
          {selectedFiles.length > 0 && (
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-lg flex items-center justify-between">
                  選択されたファイル
                  <Badge variant="secondary" className="ml-2">
                    {selectedFiles.length}/5
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {selectedFiles.map((uploadedFile) => (
                  <div
                    key={uploadedFile.id}
                    className="flex items-center justify-between p-3 bg-muted/50 rounded-lg border"
                  >
                    <div className="flex items-center space-x-3">
                      {getFileIcon()}
                      <div className="flex-1">
                        <p className="font-medium text-sm">
                          {uploadedFile.file.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(uploadedFile.file.size)}
                        </p>
                      </div>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(uploadedFile.id)}
                      disabled={isUploading}
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* アップロードボタン */}
          {selectedFiles.length > 0 && (
            <div className="pt-4">
              <Button
                onClick={handleSubmit}
                disabled={isUploading || !title.trim()}
                size="lg"
                className="w-full h-12 text-base font-medium"
              >
                {isUploading ? (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>アップロード中...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="h-5 w-5" />
                    <span>アップロード開始</span>
                  </div>
                )}
              </Button>
              
              {isUploading && (
                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>アップロード進行中...</span>
                    <span>処理中</span>
                  </div>
                  <Progress value={75} className="h-2" />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default FileUploader