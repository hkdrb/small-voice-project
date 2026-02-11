'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { BarChart2, FileText, Folder, Upload, Users, ClipboardList, MessageSquare } from "lucide-react";
import { TabsList, TabsTrigger } from "@/components/ui/Tabs";

interface DashboardTabsProps {
  activeTab: string;
  isAdmin: boolean;
  onTabChange?: (tab: string) => void;
}

export default function DashboardTabs({ activeTab, isAdmin, onTabChange }: DashboardTabsProps) {
  const router = useRouter();

  const handleTabClick = (tab: string) => {
    if (onTabChange) {
      onTabChange(tab);
    } else {
      router.push(`/dashboard?tab=${tab}`);
    }
  };

  return (
    <TabsList className="bg-white/50 p-1 rounded-xl border border-white/20 shadow-sm mb-6 w-full flex justify-start overflow-x-auto">
      {/* Admin Tabs */}
      {isAdmin && (
        <TabsTrigger
          value="analysis"
          activeTab={activeTab}
          onClick={() => handleTabClick('analysis')}
          className="flex items-center px-4 py-2 cursor-pointer"
        >
          <BarChart2 className="w-4 h-4 mr-2" />
          データ分析実行
        </TabsTrigger>
      )}

      {/* Shared Tabs */}
      <TabsTrigger
        value="reports"
        activeTab={activeTab}
        onClick={() => handleTabClick('reports')}
        className="flex items-center px-4 py-2 cursor-pointer"
      >
        <FileText className="w-4 h-4 mr-2" />
        レポート閲覧
      </TabsTrigger>

      {/* Shared Tabs - Survey Answers */}
      <TabsTrigger
        value="answers"
        activeTab={activeTab}
        onClick={() => handleTabClick('answers')}
        className="flex items-center px-4 py-2 cursor-pointer"
      >
        <Folder className="w-4 h-4 mr-2" />
        アンケート回答
      </TabsTrigger>

      {/* Everyone's Voices (Casual Chat) */}
      <TabsTrigger
        value="casual"
        activeTab={activeTab}
        onClick={() => handleTabClick('casual')}
        className="flex items-center px-4 py-2 cursor-pointer"
      >
        <MessageSquare className="w-4 h-4 mr-2" />
        雑談掲示板
      </TabsTrigger>

      {/* Combined Survey Management (Admin) or Requests (User) */}
      {isAdmin && (
        <TabsTrigger
          value="surveys"
          activeTab={activeTab}
          onClick={() => handleTabClick('surveys')}
          className="flex items-center px-4 py-2 cursor-pointer"
        >
          <ClipboardList className="w-4 h-4 mr-2" />
          フォーム作成・管理
        </TabsTrigger>
      )}

      {!isAdmin && (
        <TabsTrigger
          value="requests"
          activeTab={activeTab}
          onClick={() => handleTabClick('requests')}
          className="flex items-center px-4 py-2 cursor-pointer"
        >
          <Upload className="w-4 h-4 mr-2" />
          フォーム申請
        </TabsTrigger>
      )}

      {/* Admin Only Tabs */}
      {isAdmin && (
        <>
          <TabsTrigger
            value="import"
            activeTab={activeTab}
            onClick={() => handleTabClick('import')}
            className="flex items-center px-4 py-2 cursor-pointer"
          >
            <Upload className="w-4 h-4 mr-2" />
            CSVインポート
          </TabsTrigger>
          <TabsTrigger
            value="members"
            activeTab={activeTab}
            onClick={() => handleTabClick('members')}
            className="flex items-center px-4 py-2 cursor-pointer"
          >
            <Users className="w-4 h-4 mr-2" />
            メンバーリスト
          </TabsTrigger>
        </>
      )}
    </TabsList>
  );
}
