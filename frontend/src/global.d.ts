import { JSX } from "solid-js";

declare module "solid-js" {
  namespace JSX {
    interface IntrinsicElements {
      // Name your element and define its allowed attributes
      "ot-table": JSX.HTMLAttributes<HTMLElement> & {
        "empty-text"?: string; 
      };
      "ot-dropdown": JSX.HTMLAttributes<HTMLElement>;
    }
  }
}