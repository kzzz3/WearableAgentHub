import { useState, useEffect } from "react";

export function TimeDisplay() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const hours = time.getHours().toString().padStart(2, "0");
  const minutes = time.getMinutes().toString().padStart(2, "0");
  const seconds = time.getSeconds().toString().padStart(2, "0");

  const dayNames = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  const day = dayNames[time.getDay()];
  const date = time.getDate().toString().padStart(2, "0");

  return (
    <div className="text-center select-none">
      <div className="font-mono text-hud-accent text-2xl font-bold tracking-wider leading-none">
        {hours}:{minutes}
        <span className="text-hud-muted text-xs ml-1">{seconds}</span>
      </div>
      <div className="text-[9px] text-hud-muted mt-0.5 tracking-widest font-mono">
        {day} {date}
      </div>
    </div>
  );
}