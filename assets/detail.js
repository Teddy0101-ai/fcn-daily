async function loadJson(path){
  const res = await fetch(path + "?t=" + Date.now());
  if(!res.ok) throw new Error("Failed to load " + path);
  return await res.json();
}

function getId(){
  return new URLSearchParams(location.search).get("id");
}

function safe(v){ return (v ?? "") === "" ? "-" : v; }

async function renderDetail(){
  const id = getId();
  const [meta, details] = await Promise.all([
    loadJson("data/meta.json"),
    loadJson("data/details.json")
  ]);
  const item = details[id];
  if(!item){
    document.getElementById("pageTitle").textContent = "选品详情";
    document.getElementById("content").innerHTML = `<div class="card main-card">未找到对应产品。</div>`;
    return;
  }

  document.title = `${item.underlying_display} - 选品详情`;
  document.getElementById("pageTitle").textContent = meta.detail_title_cn || "选品详情";

  document.getElementById("content").innerHTML = `
    <div class="product-type">${item.product_type_en || meta.product_type_en_default || "Fixed Coupon Note"}</div>
    <h1 class="detail-name">${item.underlying_display}</h1>

    <div class="metrics">
      <div class="metric">
        <div class="value red">${item.coupon_display}</div>
        <div class="label">票息(年化)</div>
      </div>
      <div class="metric">
        <div class="value">${item.strike_display}</div>
        <div class="label">执行价格</div>
      </div>
      <div class="metric">
        <div class="value">${item.ko_display}</div>
        <div class="label">敲出价格</div>
      </div>
      <div class="metric">
        <div class="value">${safe(item.tenor)}</div>
        <div class="label">期限</div>
      </div>
    </div>
    <div class="quote-time">报价时间：${safe(item.quote_time)}</div>

    <div class="section-title">选品详情</div>
    <div class="card main-card">
      <div class="detail-grid">
        <div class="k">挂钩标的</div><div>${safe(item.underlying_detail_display)}</div>
        <div class="k">期限</div><div>${safe(item.tenor)}</div>
        <div class="k">锁定期限</div><div>${safe(item.lock_period)}</div>
        <div class="k">票息(年化)</div><div>${safe(item.coupon_display)}</div>
        <div class="k">执行价格</div><div>${safe(item.strike_display)}</div>
        <div class="k">敲出价格</div><div>${safe(item.ko_display)}</div>
        <div class="k">敲出类型</div><div>${safe(item.ko_type_cn)}</div>
        <div class="k">敲入价格</div><div>${safe(item.ki_display)}</div>
        <div class="k">敲入类型</div><div>${safe(item.ki_type_cn)}</div>
        <div class="k">货币类型</div><div>${safe(item.currency)}</div>
      </div>
      <div class="disclaimer" style="margin-top:20px">注：“每日”代表每日观察是否敲出。</div>
    </div>

    <div class="card advisor-card">
      <div class="avatar" id="advisorAvatarText">${meta.advisor_avatar_text || "点击此处\n上传个人头像"}</div>
      <div class="advisor-name">${meta.advisor_name || "Ryan Yi 易俊融"}</div>
      <div>
        <div class="qr-box"></div>
        <div class="qr-caption">${meta.qr_caption || "长按扫码 咨询申购"}</div>
      </div>
    </div>
  `;

  const shareBtn = document.getElementById("shareBtn");
  shareBtn.addEventListener("click", async () => {
    if (navigator.share) {
      try {
        await navigator.share({title: item.underlying_display, url: location.href});
      } catch (_) {}
    } else {
      await navigator.clipboard.writeText(location.href);
      alert("链接已复制");
    }
  }, {once:true});
}

document.addEventListener("DOMContentLoaded", renderDetail);
