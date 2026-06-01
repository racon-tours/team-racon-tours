/* team.racon.tours — profile.js
   Reads /data/roster.json and renders link sections for the slug
   declared on the host element (#link-sections data-slug). */
(function () {
  "use strict";

  const host = document.getElementById("link-sections");
  if (!host) return;
  const slug = host.dataset.slug;
  if (!slug) return;

  const isHttpUrl = (s) => /^https?:\/\//i.test(s || "");

  // safe-attribute escape (for URLs only; titles/subs come from a trusted sheet
  // editor and contain intentional HTML entities like &mdash;)
  const esc = (s) => String(s).replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[c]));

  fetch("/data/roster.json", { cache: "no-cache" })
    .then(r => {
      if (!r.ok) throw new Error("roster fetch failed: " + r.status);
      return r.json();
    })
    .then(data => render(data))
    .catch(err => {
      host.innerHTML =
        '<p class="loading" role="alert">Couldn’t load links right now. ' +
        'Please try again in a moment.</p>';
      console.error(err);
    });

  function render(data) {
    const links = (data.links || [])
      .filter(l => (l.slug || "").trim() === slug)
      .filter(l => isHttpUrl(l.url));

    if (!links.length) {
      host.innerHTML = '<p class="loading">No links yet.</p>';
      return;
    }

    // Group by section, preserving first-appearance order.
    const order = [];
    const groups = new Map();
    for (const l of links) {
      const section = (l.section || "").trim();
      if (!groups.has(section)) {
        groups.set(section, []);
        order.push(section);
      }
      groups.get(section).push(l);
    }

    const parts = [];
    for (const section of order) {
      parts.push(`<h2 class="section-title">${section}</h2>`);
      for (const l of groups.get(section)) {
        const title = (l.title || "").trim();
        const sub   = (l.subtitle || "").trim();
        const subHtml = sub
          ? `<span class="link__sub">${sub}</span>`
          : "";
        parts.push(
          `<a class="link" href="${esc(l.url)}" target="_blank" rel="noopener">` +
            `<span class="link__body">` +
              `<span class="link__title">${title}</span>${subHtml}` +
            `</span>` +
            `<span class="link__arrow">&#8599;</span>` +
          `</a>`
        );
      }
    }
    host.innerHTML = parts.join("\n");
  }
})();
