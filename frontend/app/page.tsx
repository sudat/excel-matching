import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  FileSpreadsheet,
  ArrowRight,
  Star,
  Database,
  Upload,
  Search,
  Target,
  Zap,
  Shield,
} from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  const features = [
    {
      icon: <Zap className="h-8 w-8 text-blue-600" />,
      title: "AI自動解析",
      description: "機械学習による高精度なデータマッチングで業務を自動化",
    },
    {
      icon: <Target className="h-8 w-8 text-green-600" />,
      title: "高精度突合",
      description: "複雑な照合ルールにも対応した柔軟な突合処理",
    },
    {
      icon: <Shield className="h-8 w-8 text-purple-600" />,
      title: "セキュア処理",
      description: "企業レベルのセキュリティでデータを安全に管理",
    },
  ];

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
                <h1 className="text-xl font-bold text-gray-900">
                  経費精算突合システム
                </h1>
                <p className="text-sm text-gray-600">Excel Matching System</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="hidden sm:flex">
                v0.1.0
              </Badge>
              <Link href="/dashboard">
                <Button size="sm">
                  ダッシュボードへ
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full max-w-7xl mx-auto px-4 py-12">
        {/* ヒーローセクション */}
        <section className="text-center mb-16">
          <div className="max-w-4xl mx-auto">
            <h2 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Excel照合を
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                スマートに
              </span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed max-w-3xl mx-auto">
              経費精算データとExcelファイルの突合処理をAIが自動化。
              複雑な照合作業を効率化し、正確性を向上させます。
            </p>

            {/* 機能ハイライト */}
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500 mb-8">
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>最大5ファイル対応</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-gray-300"></div>
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>AI自動照合</span>
              </div>
              <div className="hidden sm:block w-px h-4 bg-gray-300"></div>
              <div className="flex items-center space-x-1">
                <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                <span>セキュア処理</span>
              </div>
            </div>

            {/* CTAボタン */}
            <div className="flex justify-center">
              <Link href="/dashboard">
                <Button size="lg" className="text-lg px-8 py-3">
                  <Database className="h-5 w-5 mr-2" />
                  今すぐ始める
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* 特徴セクション */}
        <section className="mb-16">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-gray-900 mb-4">
              なぜ選ばれるのか
            </h3>
            <p className="text-gray-600 max-w-2xl mx-auto">
              従来の手作業による照合作業を革新する、最新AI技術を活用したスマートソリューション
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card
                key={index}
                className="text-center hover:shadow-lg transition-shadow duration-300"
              >
                <CardContent className="p-8">
                  <div className="flex justify-center mb-4">
                    <div className="h-16 w-16 bg-gradient-to-br from-gray-50 to-gray-100 rounded-full flex items-center justify-center">
                      {feature.icon}
                    </div>
                  </div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-3">
                    {feature.title}
                  </h4>
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
                  </p>
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
              段階的なワークフローで、誰でも確実にExcel照合作業を自動化できます。
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-full flex items-center justify-center text-xl font-bold mb-4 mx-auto">
                01
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                仕訳データ管理
              </h4>
              <p className="text-gray-600 text-sm leading-relaxed">
                会計システムから出力した仕訳データ（CSV）をアップロードし、システムに登録。一覧表示や検索で管理します。
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-green-600 to-green-700 text-white rounded-full flex items-center justify-center text-xl font-bold mb-4 mx-auto">
                02
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                Excelアップロード
              </h4>
              <p className="text-gray-600 text-sm leading-relaxed">
                各部門から提供されたExcel/CSVファイルをアップロード。AIが自動でファイル構造を解析し、照合準備を行います。
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-purple-700 text-white rounded-full flex items-center justify-center text-xl font-bold mb-4 mx-auto">
                03
              </div>
              <h4 className="text-lg font-semibold text-gray-900 mb-2">
                突合・照合実行
              </h4>
              <p className="text-gray-600 text-sm leading-relaxed">
                登録済み仕訳データとExcelファイルの自動突合処理を実行。詳細な分析結果とレポートをダウンロード可能です。
              </p>
            </div>
          </div>
        </section>

        {/* CTA セクション */}
        <section className="mb-16">
          <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-0">
            <CardContent className="p-12">
              <div className="text-center max-w-3xl mx-auto">
                <h3 className="text-3xl font-bold text-gray-900 mb-4">
                  今すぐ始めてみませんか？
                </h3>
                <p className="text-gray-600 mb-8 text-lg">
                  面倒な Excel 照合作業を AI にお任せください。
                  数分でセットアップが完了し、すぐに効率化を実感できます。
                </p>
                <div className="flex justify-center">
                  <Link href="/dashboard">
                    <Button size="lg" className="text-lg px-8 py-3">
                      <Database className="h-5 w-5 mr-2" />
                      ダッシュボードを開く
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* サポート情報セクション */}
        <section>
          <Card className="bg-gradient-to-r from-gray-50 to-slate-50 border-0">
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
                  <Button size="lg">サポートに連絡</Button>
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
              © 2024 経費精算突合システム. All rights reserved.
            </p>
            <p className="text-xs mt-2">
              Powered by Next.js and Advanced AI Technology
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
