import type { Metadata } from "next";
import "./globals.css";
import { SidebarProvider } from "@/components/SidebarContext";
import SidebarWrapper from "@/components/SidebarWrapper";

export const metadata: Metadata = {
  title: "Small Voice",
  description: "Small Voice Project",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body className="flex h-screen overflow-hidden bg-slate-50">
        <SidebarProvider>
          <SidebarWrapper />
          <main className="flex-1 overflow-y-auto relative">
            {children}
          </main>
        </SidebarProvider>
      </body>
    </html>
  );
}
