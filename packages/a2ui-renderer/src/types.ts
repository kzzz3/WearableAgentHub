export interface A2UIMessage {
  type: "createSurface" | "updateComponents" | "destroySurface";
  surfaceId?: string;
  presentation?: { mode: string };
  components?: A2UIComponent[];
}

export interface A2UIComponent {
  id: string;
  type: "Text" | "Card" | "List" | "ListItem" | "StatusBar" | "Divider" | "Badge";
  props: Record<string, any>;
  children?: A2UIComponent[];
}
