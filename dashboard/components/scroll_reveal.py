"""Reusable scroll-reveal: sections fade + rise as they enter the viewport.

WHY JS (and why it is safe on Streamlit Community Cloud):
    A pure-CSS scroll-timeline reveal is scrubbed by scroll POSITION, so fast /
    mouse-wheel scrollers blow past it and it only runs on very recent Chromium.
    A fixed-duration, time-based fade needs a trigger, and the only way to reach
    the page's sections from Streamlit is a component iframe. `components.html`
    renders a same-origin `srcdoc` iframe (it inherits the app origin), so
    `window.parent.document` is reachable both locally AND on Streamlit
    Community Cloud — the standard pattern behind community JS recipes.

ROBUSTNESS:
    * Fail-safe — sections default to visible (CSS has no hidden state until the
      observer adds `.reveal-off`); if the script is ever blocked the page still
      shows everything, never blank.
    * Re-triggers — fades in on entry, resets on exit, so scrolling back up and
      down replays the reveal.
    * Reduced motion — reveals everything with no transition.
    * Survives Streamlit reruns — the component remounts and re-observes; a
      retry loop covers content that mounts slightly later on slower hosts.

USAGE: call render_scroll_reveal(<css selector for the sections>) once at the
    end of a page, and put a `reveal` class (or a keyed container) on each
    section. See components/styles.py `.reveal-off` for the hidden state.
"""

from __future__ import annotations

import streamlit.components.v1 as components

from dashboard.services.data_loader import load_theme

# __SEL__ / __MS__ / __EASE__ are substituted per call. Everything is wrapped in
# try/catch and a same-origin guard, so a blocked parent simply leaves the
# sections visible.
_SCRIPT = """
<script>
(function () {
  try {
    var pwin = window.parent, pdoc = pwin && pwin.document;
    if (!pdoc) return;
    var SEL = '__SEL__';
    var TRANS = 'opacity __MS__ms __EASE__, transform __MS__ms __EASE__';
    var reduce = pwin.matchMedia
      && pwin.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var hide = function (el) {
      el.style.transition = 'none';
      el.classList.add('reveal-off');
      void el.offsetWidth;
      el.style.transition = TRANS;
    };
    var setup = function () {
      var nodes = pdoc.querySelectorAll(SEL);
      if (!nodes.length) return false;
      if (reduce || !pwin.IntersectionObserver) {
        nodes.forEach(function (n) {
          n.classList.remove('reveal-off'); n.style.transition = '';
        });
        return true;
      }
      if (pwin.__revObs) { try { pwin.__revObs.disconnect(); } catch (e) {} }
      // Reveal as soon as a section is a little above the bottom edge (it fades
      // in over the fixed duration as it rises); hide once it has left. The -10%
      // bottom margin means a section still peeking at the very bottom on load
      // stays hidden and reveals on the first scroll — while the last section,
      // lifted clear by the page's bottom padding, always crosses the margin and
      // is never left stuck. Simple observe (no first-fire skip) so a fast jump
      // to a section can never eat its reveal.
      var obs = new pwin.IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) e.target.classList.remove('reveal-off');
          else hide(e.target);
        });
      }, { threshold: 0, rootMargin: '0px 0px -10% 0px' });
      pwin.__revObs = obs;
      nodes.forEach(function (n) { n.style.transition = TRANS; obs.observe(n); });
      return true;
    };
    var tries = 0, t = pwin.setInterval(function () {
      if (setup() || ++tries > 80) pwin.clearInterval(t);
    }, 60);
  } catch (e) { /* parent unreachable: sections stay visible (CSS default) */ }
})();
</script>
"""


def render_scroll_reveal(selector: str = ".reveal") -> None:
    """Inject the reveal observer for `selector` (0-height, invisible component).

    `selector` must not contain a single quote (double quotes are fine).
    """
    motion = load_theme().get("motion", {})
    ms = int(motion.get("business_reveal_ms", 720))
    ease = motion.get("easing", "ease-out")
    html = (
        _SCRIPT.replace("__SEL__", selector)
        .replace("__MS__", str(ms))
        .replace("__EASE__", ease)
    )
    components.html(html, height=0)
