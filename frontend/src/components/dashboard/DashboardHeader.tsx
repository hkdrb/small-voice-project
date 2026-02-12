'use client';

import React from 'react';
import { LayoutDashboard, ArrowLeft } from "lucide-react";
import Link from 'next/link';
import NotificationBell from './NotificationBell';

interface DashboardHeaderProps {
  title?: string;
  icon?: React.ReactNode;
  showBack?: boolean;
  backHref?: string;
}

export default function DashboardHeader({
  title = "ダッシュボード",
  icon = <LayoutDashboard className="h-5 w-5" />,
  showBack = false,
  backHref = "/dashboard"
}: DashboardHeaderProps) {
  return (
    <header className="h-16 flex items-center justify-between px-4 md:px-6 border-b border-white/40 shrink-0 bg-white/50 backdrop-blur-sm sticky top-0 z-10 w-full pl-[72px] md:pl-6">
      <div className="flex items-center">
        {showBack && (
          <Link href={backHref} className="mr-3 md:mr-4 text-slate-400 hover:text-sage-dark transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </Link>
        )}
        <h1 className="text-lg md:text-xl font-bold text-sage-dark flex items-center gap-2">
          {icon}
          {title}
        </h1>
      </div>
      <div className="flex items-center gap-2 md:gap-4">
        <NotificationBell />
      </div>
    </header>
  );
}
