import React from 'react';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (id: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex space-x-1 border-b border-gray-200/50 mb-6 overflow-x-auto">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={`
              flex items-center px-4 py-3 text-sm font-medium transition-all duration-200 border-b-2 whitespace-nowrap
              ${isActive
                ? 'border-sage-primary text-sage-dark bg-white/40'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-white/20'
              }
            `}
          >
            {tab.icon && <span className="mr-2">{tab.icon}</span>}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}

export function TabsList({ children, className }: { children: React.ReactNode, className?: string }) {
  return <div className={className}>{children}</div>;
}

export function TabsTrigger({ value, activeTab, onClick, children, className }: any) {
  const isActive = value === activeTab;
  return (
    <button
      onClick={onClick}
      className={`${className} ${isActive ? 'bg-white shadow-sm text-sage-dark font-bold' : 'text-slate-500 hover:text-sage-dark hover:bg-white/30'} transition-all rounded-lg whitespace-nowrap`}
    >
      {children}
    </button>
  );
}
