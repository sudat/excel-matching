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

interface UploadedFile {
  file: File
  id: string
}

interface FileUploaderProps {
  onUpload: (title: string, description: string, files: File[]) => Promise<void>
  isUploading: boolean
}

const FileUploader: React.FC<FileUploaderProps> = ({ onUpload, isUploading }) => {
  const [dragActive, setDragActive] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<UploadedFile[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [errors, setErrors] = useState<string[]>([])
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
    
    try {
      await onUpload(title, description, files)
      // アップロード成功後、フォームをリセット
      setTitle('')
      setDescription('')
      setSelectedFiles([])
      setErrors([])
    } catch (error) {
      console.error('Upload failed:', error)
    }
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