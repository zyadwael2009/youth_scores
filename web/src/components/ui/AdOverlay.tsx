'use client';
import { useApp } from '@/context/AppContext';
import AdInterstitial from './AdInterstitial';

export default function AdOverlay() {
  const { pendingAd, clearAd } = useApp();
  if (!pendingAd) return null;
  return <AdInterstitial ad={pendingAd} onClose={clearAd} />;
}
