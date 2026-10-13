import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Check } from "lucide-react";

/** Close on outside pointer-down and Escape. `refs` are the elements that count as "inside". */
export function useDismiss(open, onClose, refs) {
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    if (!open) return undefined;
    const onDown = (e) => {
      if (refs.some((r) => r.current?.contains(e.target))) return;
      closeRef.current({ restoreFocus: false });
    };
    const onKey = (e) => { if (e.key === "Escape") { e.stopPropagation(); closeRef.current({ restoreFocus: true }); } };
    document.addEventListener("pointerdown", onDown);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("pointerdown", onDown); document.removeEventListener("keydown", onKey); };
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps
}

/** Arrow-key / Home / End navigation between [role^=menuitem] children; focuses the first item on open. */
export function useMenuKeys(open, listRef) {
  useEffect(() => {
    if (!open) return;
    const t = setTimeout(() => {
      const items = listRef.current?.querySelectorAll('[role^="menuitem"]:not([disabled])');
      const checked = listRef.current?.querySelector('[aria-checked="true"]');
      (checked ?? items?.[0])?.focus();
    }, 0);
    return () => clearTimeout(t);
  }, [open, listRef]);
  return useCallback((e) => {
    const items = [...(listRef.current?.querySelectorAll('[role^="menuitem"]:not([disabled])') ?? [])];
    if (!items.length) return;
    const i = items.indexOf(document.activeElement);
    const go = (n) => { e.preventDefault(); items[(n + items.length) % items.length].focus(); };
    if (e.key === "ArrowDown") go(i + 1);
    else if (e.key === "ArrowUp") go(i - 1);
    else if (e.key === "Home") go(0);
    else if (e.key === "End") go(items.length - 1);
    else if (e.key === "Tab") e.preventDefault();
  }, [listRef]);
}

/**
 * Floating panel anchored to an element, rendered in a portal with fixed positioning so it is never
 * clipped by scrolling containers, and clamped to stay inside the viewport.
 * placement: "bottom-start" | "bottom-end" | "top-start" | "right-start"
 */
export function Floating({ anchorRef, open, placement = "bottom-start", offset = 8, caret = false, className = "", children, panelRef, ...rest }) {
  const localRef = useRef(null);
  const ref = panelRef ?? localRef;
  const [pos, setPos] = useState(null);

  useLayoutEffect(() => {
    if (!open) { setPos(null); return undefined; }
    const place = () => {
      const a = anchorRef.current?.getBoundingClientRect();
      const p = ref.current?.getBoundingClientRect();
      if (!a || !p) return;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const m = 8;
      let top; let left;
      if (placement.startsWith("right")) { left = a.right + offset; top = a.top - 6; }
      else if (placement.startsWith("top")) { top = a.top - offset - p.height; left = placement.endsWith("end") ? a.right - p.width : a.left; }
      else { top = a.bottom + offset; left = placement.endsWith("end") ? a.right - p.width : a.left; }
      if (placement.startsWith("bottom") && top + p.height > vh - m && a.top - offset - p.height > m) top = a.top - offset - p.height;
      left = Math.max(m, Math.min(left, vw - p.width - m));
      top = Math.max(m, Math.min(top, vh - p.height - m));
      const caretX = Math.max(14, Math.min(a.left + a.width / 2 - left, p.width - 14));
      const above = top + p.height <= a.top;
      setPos({ top, left, caretX, above });
    };
    place();
    window.addEventListener("resize", place);
    window.addEventListener("scroll", place, true);
    return () => { window.removeEventListener("resize", place); window.removeEventListener("scroll", place, true); };
  }, [open, placement, offset, anchorRef, ref]);

  if (!open) return null;
  return createPortal(
    <div ref={ref} {...rest}
      style={{ position: "fixed", top: pos?.top ?? -9999, left: pos?.left ?? -9999, visibility: pos ? "visible" : "hidden" }}
      className={`popover pop-in z-[55] ${className}`}>
      {caret && pos && !placement.startsWith("right") && (
        <span aria-hidden="true" className={`popover-caret ${pos.above ? "popover-caret-down" : "popover-caret-up"}`} style={{ left: pos.caretX - 6 }} />
      )}
      {children}
    </div>,
    document.body,
  );
}

/**
 * Button + dropdown menu. `items`: [{id, label, description?, icon?, disabled?, divider?, dot?}].
 * With `value`, items render as menuitemradio and show a check on the selected one.
 */
export function MenuButton({
  label, items, value, onSelect, renderButton, header, placement = "bottom-start", caret = false, menuLabel, className = "",
  width = "w-56", footer,
}) {
  const [open, setOpen] = useState(false);
  const btnRef = useRef(null);
  const listRef = useRef(null);
  const close = useCallback(({ restoreFocus } = {}) => { setOpen(false); if (restoreFocus) btnRef.current?.focus(); }, []);
  useDismiss(open, close, [btnRef, listRef]);
  const onKeyDown = useMenuKeys(open, listRef);
  const radio = value !== undefined;

  return (
    <>
      {renderButton({
        ref: btnRef, open,
        props: {
          "aria-haspopup": "menu", "aria-expanded": open, "aria-label": label,
          onClick: () => setOpen((o) => !o),
          onKeyDown: (e) => { if ((e.key === "ArrowDown" || e.key === "ArrowUp") && !open) { e.preventDefault(); setOpen(true); } },
        },
      })}
      <Floating anchorRef={btnRef} panelRef={listRef} open={open} placement={placement} caret={caret} className={`${width} ${className}`}>
        {header && <p className="px-3 pb-1 pt-2.5 text-xs font-semibold text-ink">{header}</p>}
        <div role="menu" aria-label={menuLabel ?? label} onKeyDown={onKeyDown} className="p-1.5">
          {items.map((item) => item.divider ? <div key={item.id} role="separator" className="mx-1 my-1.5 border-t border-line" /> : (
            <button key={item.id} type="button" role={radio ? "menuitemradio" : "menuitem"} aria-checked={radio ? value === item.id : undefined}
              disabled={item.disabled} tabIndex={-1}
              onClick={() => { close({ restoreFocus: !item.keepFocus }); onSelect?.(item.id, item); }}
              className="menu-item">
              {item.icon && <item.icon className="mt-0.5 h-4 w-4 shrink-0 text-muted" strokeWidth={1.6} aria-hidden="true" />}
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-1.5 text-sm text-ink">
                  <span className="truncate">{item.label}</span>
                  {item.dot && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-accent" aria-hidden="true" />}
                  {item.dot && <span className="sr-only">(recommended)</span>}
                </span>
                {item.description && <span className="mt-0.5 block text-xs text-muted">{item.description}</span>}
              </span>
              {radio && value === item.id && <Check className="mt-0.5 h-4 w-4 shrink-0 text-accent" aria-hidden="true" />}
            </button>
          ))}
        </div>
        {footer}
      </Floating>
    </>
  );
}
