'use client'

import React, { useState } from 'react'
import FileUploader from '../components/FileUploader'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  AlertCircle, 
  CheckCircle2, 
  FileSpreadsheet, 
  Database, 
  BarChart3, 
  Zap,
  ArrowRight,
  Star
} from 'lucide-react'

const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? 'http://localhost:8000' 
  : 'http://localhost:8000'

interface UploadResponse {
  status: string
  message: string
  business_request_id: string
  uploaded_files: Array<{
    file_id: string
    filename: string
    file_size: number
    file_type: string
    storage_path: string
  }>
  total_files: number
}

export default function Home() {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleUpload = async (title: string, description: string, files: File[]) => {
    setIsUploading(true)
    setError(null)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('title', title)
      if (description) {
        formData.append('description', description)
      }
      
      files.forEach((file) => {
        formData.append('files', file)
      })

      const response = await fetch(`${API_BASE_URL}/upload/business-request`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'アップロードに失敗しました')
      }

      const result: UploadResponse = await response.json()
      setUploadResult(result)
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'アップロード中にエラーが発生しました')
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const features = [
    {
      icon: <FileSpreadsheet className="h-8 w-8 text-blue-600" />,
      title: "多形式対応",
      description: "Excel（.xlsx/.xls）およびCSVファイルをサポート"
    },
    {
      icon: <Database className="h-8 w-8 text-green-600" />,
      title: "安全な保存",
      description: "Supabase Storageによる高セキュリティなファイル管理"
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-purple-600" />,
      title: "高度な分析",
      description: "AIによるデータ解析とマッチング機能"
    },
    {
      icon: <Zap className="h-8 w-8 text-yellow-600" />,
      title: "高速処理",
      description: "最適化されたエンジンによる迅速なデータ処理"
    }
  ]

  const steps = [
    {
      number: "01", 
      title: "ファイルアップロード",
      description: "業務依頼のタイトルを入力し、分析対象のExcel/CSVファイルをドラッグ&ドロップまたは選択してアップロード"
    },
    {
      number: "02",
      title: "自動解析開始",
      description: "AIがファイル構造を解析し、最適なマッチング戦略を策定"
    },
    {
      number: "03",
      title: "結果確認",
      description: "詳細な分析結果とレポートをダウンロード可能"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50">
      {/* ヘッダーセクション */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="w-full max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Excel Matching System</h1>
                <p className="text-sm text-gray-600">Advanced Data Analysis Platform</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="hidden sm:flex">v1.0.0</Badge>
              <Button variant="outline" size="sm">
                ヘルプ
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-4 py-8">
        {/* ヒーローセクション */}
        <section className="text-center mb-12">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-6 leading-tight">
              Excel照合も
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                自動で
              </span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Excel/CSVファイルをアップロードするだけで、AIによる高度なデータ分析とマッチングを実現。
              複雑な設定は不要、直感的な操作で業務を効率化します。
            </p>
            <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>最大5ファイル対応</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-gray-300"></div>
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>10MB/ファイル</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-gray-300"></div>
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>セキュア保存</span>
              </div>
            </div>
          </div>
        </section>

        {/* アップロードセクション */}
        <section className="mb-16">
          <FileUploader 
            onUpload={handleUpload} 
            isUploading={isUploading}
          />

          {/* エラー表示 */}
          {error && (
            <div className="mt-6 max-w-4xl mx-auto px-4">
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription className="text-base">
                  {error}
                </AlertDescription>
              </Alert>
            </div>
          )}

          {/* アップロード成功表示 */}
          {uploadResult && (
            <div className="mt-6 max-w-4xl mx-auto px-4">
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <AlertDescription>
                  <div className="space-y-3">
                    <div>
                      <h3 className="font-medium text-green-800">
                        アップロード完了
                      </h3>
                      <p className="text-green-700 mt-1">
                        {uploadResult.message}
                      </p>
                    </div>
                    
                    <div className="bg-white p-4 rounded-lg border border-green-200">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-gray-700">業務依頼ID:</span>
                          <code className="ml-2 font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                            {uploadResult.business_request_id}
                          </code>
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">ファイル数:</span>
                          <span className="ml-2">{uploadResult.total_files}個</span>
                        </div>
                      </div>
                      
                      {/* アップロードファイル詳細 */}
                      <div className="mt-4">
                        <h4 className="font-medium text-gray-800 mb-3">
                          アップロードされたファイル:
                        </h4>
                        <div className="space-y-2">
                          {uploadResult.uploaded_files.map((file) => (
                            <div key={file.file_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border">
                              <div className="flex items-center space-x-3">
                                <FileSpreadsheet className="h-5 w-5 text-green-600" />
                                <div>
                                  <p className="font-medium text-gray-800 text-sm">
                                    {file.filename}
                                  </p>
                                  <p className="text-xs text-gray-500">
                                    {formatFileSize(file.file_size)}
                                  </p>
                                </div>
                              </div>
                              <Badge variant="secondary" className="text-xs">
                                完了
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="mt-4 pt-4 border-t border-green-200">
                        <Button className="w-full sm:w-auto">
                          <ArrowRight className="h-4 w-4 mr-2" />
                          分析結果を確認
                        </Button>
                      </div>
                    </div>
                  </div>
                </AlertDescription>
              </Alert>
            </div>
          )}
        </section>

        {/* 機能紹介セクション */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              なぜExcel Matching Systemを選ぶのか
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              最新のAI技術と直感的なユーザーインターフェースにより、複雑なデータ分析を誰でも簡単に実行できます。
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="border-2 hover:shadow-lg transition-all duration-200 hover:border-primary/20">
                <CardHeader className="pb-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base leading-relaxed">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* 使用方法セクション */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              簡単3ステップで完了
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              複雑な設定は一切不要。直感的な操作で、誰でも高度なデータ分析を始められます。
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {steps.map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 text-white rounded-full flex items-center justify-center text-xl font-bold mb-4 mx-auto">
                  {step.number}
                </div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  {step.title}
                </h4>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* サポート情報セクション */}
        <section>
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-0">
            <CardContent className="p-8">
              <div className="text-center max-w-2xl mx-auto">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">
                  サポートが必要ですか？
                </h3>
                <p className="text-gray-600 mb-6">
                  技術的な質問や機能に関するお問い合わせは、いつでもサポートチームまでご連絡ください。
                </p>
                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                  <Button variant="outline" size="lg">
                    ドキュメントを見る
                  </Button>
                  <Button size="lg">
                    サポートに連絡
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>

      {/* フッター */}
      <footer className="border-t bg-gray-50 mt-16">
        <div className="w-full max-w-7xl mx-auto px-4 py-8">
          <div className="text-center text-gray-600">
            <p className="text-sm">
              © 2024 Excel Matching System. All rights reserved.
            </p>
            <p className="text-xs mt-2">
              Powered by Next.js, Supabase, and Advanced AI Technology
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}