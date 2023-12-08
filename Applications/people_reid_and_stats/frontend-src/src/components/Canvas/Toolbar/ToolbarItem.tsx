import {
  CSSProperties,
  HTMLProps,
  ReactNode,
  forwardRef,
  useMemo,
} from "react";
import { useCanvas } from "src/hooks/canvas";

interface ToolbarItemProps extends HTMLProps<HTMLDivElement> {
  children: ReactNode;
  top?: string;
  left?: string;
  bottom?: string;
  right?: string;
}

export const ToolbarItem = forwardRef<HTMLDivElement, ToolbarItemProps>(
  (props, ref) => {
    const { top, left, bottom, right } = props;
    const { width, height } = useCanvas();

    const wrapperStyle = useMemo(() => {
      return {
        position: "absolute",
        width: width + "px",
        height: height + "px",
        pointerEvents: "none",
      } as CSSProperties;
    }, [width, height]);

    const itemStyle = useMemo(() => {
      const styles: CSSProperties = {
        position: "absolute",
        pointerEvents: "all",
      };

      if (top) {
        styles.top = top;
      }

      if (left) {
        styles.left = left;
      }

      if (right) {
        styles.right = right;
      }

      if (bottom) {
        styles.bottom = bottom;
      }

      return styles;
    }, [top, left, bottom, right]);

    return (
      <div style={wrapperStyle}>
        <div ref={ref} style={itemStyle}>
          {props.children}
        </div>
      </div>
    );
  }
);
