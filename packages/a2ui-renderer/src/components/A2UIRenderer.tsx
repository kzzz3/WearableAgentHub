import type { A2UIMessage, A2UIComponent } from "../types";
import { HudText } from "./HudText";
import { HudCard } from "./HudCard";
import { HudList } from "./HudList";
import { HudStatusBar } from "./HudStatusBar";

function renderComponent(comp: A2UIComponent): React.ReactNode {
  switch (comp.type) {
    case "Text":
      return <HudText key={comp.id} content={comp.props.content || ""} variant={comp.props.variant || "body"} />;
    case "Card":
      return (
        <HudCard key={comp.id} title={comp.props.title} subtitle={comp.props.subtitle}>
          {comp.children?.map(renderComponent)}
        </HudCard>
      );
    case "List":
      return <HudList key={comp.id} items={comp.props.items || []} />;
    case "ListItem":
      return (
        <div key={comp.id} className="text-sm text-hud-text animate-fade-in">
          {comp.props.left && <span className="text-hud-accent">{comp.props.left} </span>}
          <span>{comp.props.primary}</span>
          {comp.props.right && <span className="text-hud-muted ml-2">{comp.props.right}</span>}
        </div>
      );
    case "StatusBar":
      return <HudStatusBar key={comp.id} items={comp.props.items || []} />;
    case "Divider":
      return <hr key={comp.id} className="border-hud-accent/10 my-2" />;
    case "Badge":
      return (
        <span key={comp.id} className={`inline-block text-xs px-2 py-0.5 rounded-full ${comp.props.className || "bg-hud-accent/20 text-hud-accent"}`}>
          {comp.props.text}
        </span>
      );
    default:
      return <div key={comp.id} className="text-hud-muted text-xs">[{comp.type}]</div>;
  }
}

export function A2UIRenderer({ messages }: { messages: A2UIMessage[] }) {
  return (
    <div className="space-y-3">
      {messages.map((msg, i) => {
        if (msg.type === "updateComponents" && msg.components) {
          return <div key={msg.surfaceId || i}>{msg.components.map(renderComponent)}</div>;
        }
        return null;
      })}
    </div>
  );
}
