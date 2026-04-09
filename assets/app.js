const DATA_FILES = {
  highlight: "data/highlight.json",
  usd: "data/usd.json",
  hkd: "data/hkd.json",
  meta: "data/meta.json"
};

const state = {
  tab: "highlight",
  records: {
    highlight: [],
    usd: [],
    hkd: []
  },
  meta: {}
};

function splitUnderlyingForDisplay(text) {
  if (!text) return "";
  return text
    .split("+")
    .map(s => s.trim())
    .filter(Boolean)
    .join("<br>");
}

function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatUnderlyingHtml(text) {
  return splitUnderlyingForDisplay(escapeHtml(text));
}

function getDetailLink(item) {
  return `detail.html?id=${encodeURIComponent(item.id || "")}`;
}

function renderRows(items) {
  const tbody = document.getElementById("product-tbody");

  if (!items || !items.length) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="padding:16px 4px;color:#999;font-size:12px;">暂无数据</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = items.map(item => `
    <tr>
      <td class="name-cell">${formatUnderlyingHtml(item.underlying_display || "")}</td>
      <td class="value-cell">${escapeHtml(item.ko_display || "")}</td>
      <td class="value-cell">${escapeHtml(item.strike_display || "")}</td>
      <td class="value-cell">${escapeHtml(item.tenor || "")}</td>
      <td class="value-cell">${escapeHtml(item.coupon_display || "")}</td>
      <td class="value-cell"><a class="detail-link" href="${getDetailLink(item)}">详情</a></td>
    </tr>
  `).join("");
}

function applyMeta(meta) {
  if (!meta) return;

  const title = document.getElementById("site-title");
  const disclaimer = document.getElementById("disclaimer");
  const advisorName = document.getElementById("advisor-name");

  if (title && meta.site_title_cn) title.textContent = meta.site_title_cn;
  if (disclaimer && meta.disclaimer_cn) disclaimer.textContent = meta.disclaimer_cn;
  if (advisorName && meta.advisor_name) advisorName.textContent = meta.advisor_name;
}

function setActiveTab(tab) {
  state.tab = tab;

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  });

  renderRows(state.records[tab] || []);
}

async function loadJson(path) {
  const res = await fetch(`${path}?t=${Date.now()}`);
  if (!res.ok) {
    throw new Error(`Failed to load ${path}`);
  }
  return res.json();
}

async function init() {
  try {
    const [highlight, usd, hkd, meta] = await Promise.all([
      loadJson(DATA_FILES.highlight),
      loadJson(DATA_FILES.usd),
      loadJson(DATA_FILES.hkd),
      loadJson(DATA_FILES.meta)
    ]);

    state.records.highlight = highlight || [];
    state.records.usd = usd || [];
    state.records.hkd = hkd || [];
    state.meta = meta || {};

    applyMeta(state.meta);
    setActiveTab("highlight");
  } catch (err) {
    console.error(err);
    renderRows([]);
  }
}

document.addEventListener("click", async (e) => {
  const tabBtn = e.target.closest(".tab-btn");
  if (tabBtn) {
    setActiveTab(tabBtn.dataset.tab);
    return;
  }

  const shareBtn = e.target.closest("#share-btn");
  if (shareBtn) {
    const shareData = {
      title: document.title,
      text: "热门选品",
      url: window.location.href
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (err) {}
    } else {
      try {
        await navigator.clipboard.writeText(window.location.href);
        alert("链接已复制");
      } catch (err) {
        alert(window.location.href);
      }
    }
  }
});

init();
