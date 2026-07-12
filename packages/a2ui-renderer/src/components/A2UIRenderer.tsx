import type { A2UIMessage, A2UIComponent } from "../types";
import { HudText } from "./HudText";
import { HudCard } from "./HudCard";
import { HudList } from "./HudList";
import { HudStatusBar } from "./HudStatusBar";

function renderComponent(idx: number, comp: A2UIComponent): React.ReactNode {
  const key = `${idx}-${comp.id || comp.type}`;

  switch (comp.type) {
    case "Text":
      return <HudText key={key} content={comp.props.content || ""} variant={comp.props.variant || "body"} />;
    case "Card":
      return (
        <HudCard key={key} title={comp.props.title} subtitle={comp.props.subtitle}>
          {comp.children?.map((child, ci) => renderComponent(ci, child))}
        </HudCard>
      );
    case "List":
      return <HudList key={key} items={comp.props.items || []} />;
    case "ListItem":
      return (
        <div key={key} className="text-sm text-hud-text animate-fade-in">
          {comp.props.left && <span className="text-hud-accent">{comp.props.left} </span>}
          <span>{comp.props.primary}</span>
          {comp.props.right && <span className="text-hud-muted ml-2">{comp.props.right}</span>}
        </div>
      );
    case "StatusBar":
      return <HudStatusBar key={key} items={comp.props.items || []} />;
    case "Divider":
      return <hr key={key} className="border-hud-accent/10 my-2" />;
    case "Badge":
      return (
        <span key={key} className={`inline-block text-xs px-2 py-0.5 rounded-full ${comp.props.className || "bg-hud-accent/20 text-hud-accent"}`}>
          {comp.props.text}
        </span>
      );
    default:
      return <div key={key} className="text-hud-muted text-xs">[{comp.type}]</div>;
  }
}

export function A2UIRenderer({ messages }: { messages: A2UIMessage[] }) {
  return (
    <div className="space-y-3">
      {messages.map((msg, i) => {
        if (msg.type === "updateComponents" && msg.components) {
          const wrapperKey = `${i}-${msg.surfaceId || "surface"}`;
          return (
            <div key={wrapperKey} className="space-y-2">
              {msg.components.map((comp, ci) => renderComponent(ci, comp))}
            </div>
          );
        }
        return null;
      })}
    </div>
  );
}
