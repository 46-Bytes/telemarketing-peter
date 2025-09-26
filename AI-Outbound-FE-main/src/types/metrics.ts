import { ReactNode } from 'react';

export interface Metric {
  id: string;
  title: string;
  value: string | number | ReactNode;
  icon: ReactNode;
  color: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
} 