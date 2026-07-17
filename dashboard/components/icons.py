"""Local inline SVG registry for dashboard presentation components."""

from __future__ import annotations

import html

_PATHS: dict[str, str] = {
    "database": '<ellipse cx="12" cy="5" rx="7" ry="3"/><path d="M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5"/><path d="M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/><path d="M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01"/>',
    "package": '<path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z"/><path d="m4.5 7.7 7.5 4.2 7.5-4.2M12 12v9"/>',
    "shield-check": '<path d="M12 22s8-3.8 8-10V5l-8-3-8 3v7c0 6.2 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/>',
    "chart-pie": '<path d="M21 12a9 9 0 1 1-9-9v9h9Z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15V3.5Z"/>',
    "brain": '<path d="M9.5 4.5A3.5 3.5 0 0 0 6 8v.4A3.4 3.4 0 0 0 4 11.5 3.5 3.5 0 0 0 7.5 15H9v5"/><path d="M14.5 4.5A3.5 3.5 0 0 1 18 8v.4a3.4 3.4 0 0 1 2 3.1 3.5 3.5 0 0 1-3.5 3.5H15v5M12 4v14M8 9h4M12 13h4"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 17l9 5 9-5"/>',
    "landmark": '<path d="m3 10 9-6 9 6H3ZM5 10v8M9 10v8M15 10v8M19 10v8M3 18h18M2 22h20"/>',
    "line-chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 6-7"/>',
    "file-search": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h8"/><path d="M14 2v6h6M9 13h3"/><circle cx="17" cy="17" r="3"/><path d="m19.2 19.2 2.3 2.3"/>',
    "file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2"/>',
    "rotate-cw": '<path d="M21 12a9 9 0 1 1-2.6-6.4L21 8"/><path d="M21 3v5h-5"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>',
    "checklist": '<path d="m3 6 2 2 4-4M3 12l2 2 4-4M3 18l2 2 4-4M13 6h8M13 12h8M13 18h8"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
}


def icon_names() -> tuple[str, ...]:
    """Return the stable registry keys for contract tests and callers."""
    return tuple(sorted(_PATHS))


def render_icon(name: str, *, size: int | None = None, class_name: str = "") -> str:
    """Return an accessible decorative SVG using the shared icon geometry."""
    if name not in _PATHS:
        raise ValueError(f"Unknown dashboard icon: {name}")
    dimension = str(int(size)) if size else "1em"
    css_class = f' class="{html.escape(class_name, quote=True)}"' if class_name else ""
    return (
        f'<svg{css_class} aria-hidden="true" focusable="false" '
        f'width="{dimension}" height="{dimension}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="1.8" '
        f'stroke-linecap="round" stroke-linejoin="round">{_PATHS[name]}</svg>'
    )


def render_icon_badge(name: str, *, class_name: str = "") -> str:
    """Wrap a registry icon in the shared circular badge anatomy."""
    classes = "icon-badge" + (f" {class_name}" if class_name else "")
    return f'<span class="{html.escape(classes, quote=True)}">{render_icon(name)}</span>'

