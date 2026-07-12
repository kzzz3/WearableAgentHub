import { useState, useEffect } from "react";

interface HealthData {
  heartRate: number;
  steps: number;
  calories: number;
  spo2: number;
}

function randomDrift(value: number, min: number, max: number, delta: number): number {
  const next = value + (Math.random() - 0.5) * delta * 2;
  return Math.max(min, Math.min(max, Math.round(next)));
}

export function HealthWidget() {
  const [health, setHealth] = useState<HealthData>({
    heartRate: 72,
    steps: 4821,
    calories: 312,
    spo2: 98,
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setHealth((prev) => ({
        heartRate: randomDrift(prev.heartRate, 58, 110, 2),
        steps: prev.steps + Math.floor(Math.random() * 3),
        calories: prev.calories + (Math.random() > 0.7 ? 1 : 0),
        spo2: randomDrift(prev.spo2, 95, 100, 1),
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center justify-around w-full px-2 py-1">
      <div className="flex items-center gap-1">
        <span className="text-red-400 text-[10px] animate-heart-beat">♥</span>
        <span className="text-[9px] text-hud-text font-mono">{health.heartRate}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-hud-accent text-[10px]">👟</span>
        <span className="text-[9px] text-hud-text font-mono">{health.steps}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-hud-warning text-[10px]">🔥</span>
        <span className="text-[9px] text-hud-text font-mono">{health.calories}</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-hud-success text-[10px]">O₂</span>
        <span className="text-[9px] text-hud-text font-mono">{health.spo2}%</span>
      </div>
    </div>
  );
}