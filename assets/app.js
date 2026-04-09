async function loadJson(path){
  const res = await fetch(path + "?t=" + Date.now());
  if(!res.ok) throw new Error("Failed to load " + path);
  return await res.json();
}

function getTabFromUrl(){
  const params = new URLSearchParams(location.search);
  return params.get("tab") || "highlight";
}

function setTab(tab){
  const url = new URL(location.href);
  url.searchParams.set("tab", tab);
  history.replaceState({}, "", url);
}

function createRow(item){
  return `
    <tr>
      <td class="product-name">${item.underlying_display || ""}</td>
      <td>${item.ko_display || ""}</td>
      <td>${item.strike_display || ""}</td>
      <td>${item.tenor || ""}</td>
      <td>${item.coupon_display || ""}</td>
      <td><a class="detail-link" href="detail.html?id=${encodeURIComponent(item.id)}">详情</a></td>
    </tr>
  `;
}

async function renderList(){
  const meta = await loadJson("data/meta.json");
  const currentTab = getTabFromUrl();
  const tabMap = {
    highlight: "data/highlight.json",
    usd: "data/usd.json",
    hkd: "data/hkd.json"
  };
  const items = await loadJson(tabMap[currentTab] || tabMap.highlight);

  document.getElementById("pageTitle").textContent = meta.site_title_cn || "热门选品";
  document.getElementById("advisorName").textContent = meta.advisor_name || "Ryan Yi 易俊融";
  document.getElementById("advisorAvatarText").textContent = meta.advisor_avatar_text || "点击此处\n上传个人头像";
  document.getElementById("qrCaption").textContent = meta.qr_caption || "长按扫码 咨询申购";
  document.getElementById("disclaimer").textContent = meta.disclaimer_cn || "";

  document.getElementById("tableHead").innerHTML = `
    <tr>
      ${(meta.columns || []).map(c => `<th>${c.label}</th>`).join("")}
      <th></th>
    </tr>
  `;
  document.getElementById("tableBody").innerHTML = items.map(createRow).join("");

  const tabs = document.getElementById("tabs");
  tabs.innerHTML = (meta.tabs || []).map(tab => `
    <button class="tab ${tab.key === currentTab ? "active" : ""}" data-tab="${tab.key}">${tab.label}</button>
  `).join("");

  tabs.querySelectorAll(".tab").forEach(btn => {
    btn.addEventListener("click", () => {
      setTab(btn.dataset.tab);
      renderList();
    });
  });

  const shareBtn = document.getElementById("shareBtn");
  shareBtn.addEventListener("click", async () => {
    if (navigator.share) {
      try {
        await navigator.share({title: meta.site_title_cn || document.title, url: location.href});
      } catch (_) {}
    } else {
      await navigator.clipboard.writeText(location.href);
      alert("链接已复制");
    }
  }, {once:true});
}

document.addEventListener("DOMContentLoaded", renderList);
