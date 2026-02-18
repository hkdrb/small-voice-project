import type { Metadata } from "next";
import "./globals.css";
import { SidebarProvider } from "@/components/SidebarContext";
import SidebarWrapper from "@/components/SidebarWrapper";
import NavigationGuard from "@/components/NavigationGuard";

export const metadata: Metadata = {
  title: "Small Voice",
  description: "Small Voice Project",
};

import { Suspense } from 'react';

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="flex h-dvh overflow-hidden bg-slate-50">
        <NavigationGuard />
        <SidebarProvider>
          <Suspense fallback={<div className="hidden md:block w-64 bg-slate-50 shrink-0" />}>
            <SidebarWrapper />
          </Suspense>
          <main className="flex-1 overflow-y-auto relative">
            {children}
          </main>
        </SidebarProvider>
      </body>
    </html>
  );
}
