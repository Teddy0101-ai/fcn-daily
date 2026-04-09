function escapeHtml(text) {
  return String(text ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getQueryParam(name) {
  const url = new URL(window.location.href);
  return url.searchParams.get(name);
}

async function loadJson(path) {
  const res = await fetch(`${path}?t=${Date.now()}`);
  if (!res.ok) throw new Error(`Failed to load ${path}`);
  return res.json();
}

function appendDetailRow(container, label, value) {
  const labelEl = document.createElement("div");
  labelEl.className = "detail-label";
  labelEl.textContent = label;

  const valueEl = document.createElement("div");
  valueEl.className = "detail-value";
  valueEl.innerHTML = escapeHtml(value ?? "");

  container.appendChild(labelEl);
  container.appendChild(valueEl);
}

function fillDetail(item, meta) {
  document.title = `${item.underlying_display || "选品详情"} - 选品详情`;

  const pageTitle = document.getElementById("detail-page-title");
  const productType = document.getElementById("detail-product-type");
  const title = document.getElementById("detail-title");
  const summaryCoupon = document.getElementById("summary-coupon");
  const summaryStrike = document.getElementById("summary-strike");
  const summaryKo = document.getElementById("summary-ko");
  const summaryTenor = document.getElementById("summary-tenor");
  const quoteTime = document.getElementById("quote-time");
  const detailAdvisorName = document.getElementById("detail-advisor-name");
  const grid = document.getElementById("detail-grid");

  if (pageTitle) pageTitle.textContent = meta?.detail_title_cn || "选品详情";
  if (productType) productType.textContent = meta?.product_type_en || "Fixed Coupon Note";
  if (title) title.textContent = item.underlying_display || "选品详情";
  if (summaryCoupon) summaryCoupon.textContent = item.coupon_display || "-";
  if (summaryStrike) summaryStrike.textContent = item.strike_display || "-";
  if (summaryKo) summaryKo.textContent = item.ko_display || "-";
  if (summaryTenor) summaryTenor.textContent = item.tenor || "-";
  if (quoteTime) quoteTime.textContent = `报价时间：${item.quote_time || meta?.quote_time || "-"}`;
  if (detailAdvisorName && meta?.advisor_name) detailAdvisorName.textContent = meta.advisor_name;

  grid.innerHTML = "";

  appendDetailRow(grid, "挂钩标的", item.underlying_detail_display || item.underlying_display || "-");
  appendDetailRow(grid, "期限", item.tenor || "-");
  appendDetailRow(grid, "锁定期限", item.lock_period || "-");
  appendDetailRow(grid, "票息(年化)", item.coupon_display || "-");
  appendDetailRow(grid, "执行价格", item.strike_display || "-");
  appendDetailRow(grid, "敲出价格", item.ko_display || "-");
  appendDetailRow(grid, "敲出类型", item.ko_type_cn || "-");
  appendDetailRow(grid, "敲入价格", item.ki_display || "-");
  appendDetailRow(grid, "敲入类型", item.ki_type_cn || "无");
  appendDetailRow(grid, "货币类型", item.currency || "-");
}

async function initDetail() {
  try {
    const id = getQueryParam("id");
    const [details, meta] = await Promise.all([
      loadJson("data/details.json"),
      loadJson("data/meta.json")
    ]);

    if (!id || !details[id]) {
      document.getElementById("detail-title").textContent = "未找到产品";
      return;
    }

    fillDetail(details[id], meta);
  } catch (err) {
    console.error(err);
    document.getElementById("detail-title").textContent = "加载失败";
  }
}

document.addEventListener("click", async (e) => {
  const shareBtn = e.target.closest("#detail-share-btn");
  if (!shareBtn) return;

  const shareData = {
    title: document.title,
    text: "选品详情",
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
});

initDetail();
