// HKD <-> USD Converter 逻辑
// 实时汇率来自 open.er-api.com（免费、无需 API Key，支持浏览器跨域）。
// 接口不可用时自动回退到固定汇率 1 USD = 7.8 HKD。

const API_URL = "https://open.er-api.com/v6/latest/USD";
const FALLBACK_RATE = 7.8;

const amountInput = document.getElementById("amount");
const fromSelect = document.getElementById("from");
const toSelect = document.getElementById("to");
const swapBtn = document.getElementById("swap");
const resultBox = document.getElementById("result-box");
const resultValue = document.getElementById("result-value");
const rateLine = document.getElementById("rate-line");
const statusEl = document.getElementById("status");

let hkdPerUsd = null; // 1 USD = ? HKD
let liveRate = false;

// 统一数字显示格式
function fmtNumber(value, digits) {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

// 金额显示格式（最多两位小数）
function fmtMoney(value) {
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

// 更新底部汇率信息行
function renderRateLine() {
  if (hkdPerUsd === null) return;
  const usd2hkd = fmtNumber(hkdPerUsd, 4);
  const hkd2usd = fmtNumber(1 / hkdPerUsd, 4);
  if (liveRate) {
    rateLine.textContent = `1 USD = ${usd2hkd} HKD    |    1 HKD = ${hkd2usd} USD`;
  } else {
    rateLine.textContent = `1 USD = ${fmtNumber(hkdPerUsd, 2)} HKD (offline · fixed rate)`;
  }
}

// 联网获取实时汇率
async function loadRates() {
  rateLine.textContent = "Loading live rate…";
  statusEl.textContent = "";
  statusEl.classList.remove("error");
  try {
    const resp = await fetch(API_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    if (data.result !== "success") throw new Error("API returned an error");
    hkdPerUsd = Number(data.rates.HKD);
    liveRate = true;
  } catch (err) {
    hkdPerUsd = FALLBACK_RATE;
    liveRate = false;
    statusEl.textContent = "Could not fetch live rate, using fixed rate: " + err.message;
    statusEl.classList.add("error");
  }
  renderRateLine();
  convert(); // 汇率就绪后立即显示换算结果
}

// 执行换算
function convert() {
  const raw = amountInput.value.trim();
  if (raw === "" || Number.isNaN(Number(raw)) || Number(raw) < 0) {
    // 输入非法/为空时隐藏结果, 不弹错误提示
    resultBox.hidden = true;
    statusEl.textContent = "";
    statusEl.classList.remove("error");
    return;
  }

  const amount = Number(raw);
  const fromCcy = fromSelect.value;
  const toCcy = toSelect.value;

  // 汇率还没就绪时先取一次
  if (hkdPerUsd === null) {
    // 汇率尚未就绪, loadRates 完成后会自动触发一次换算
    return;
  }

  let result;
  if (fromCcy === toCcy) {
    result = amount;
  } else if (fromCcy === "USD") {
    result = amount * hkdPerUsd; // USD -> HKD
  } else {
    result = amount / hkdPerUsd; // HKD -> USD
  }

  resultValue.textContent = `${fmtMoney(result)} ${toCcy}`;
  resultBox.hidden = false;
  statusEl.textContent = "";
  statusEl.classList.remove("error");
}

// 互换币种
function swap() {
  const f = fromSelect.value;
  fromSelect.value = toSelect.value;
  toSelect.value = f;
}

// 事件绑定：输入金额或切换币种时立即换算, 无需按钮
amountInput.addEventListener("input", convert);
fromSelect.addEventListener("change", convert);
toSelect.addEventListener("change", convert);
swapBtn.addEventListener("click", () => {
  swap();
  convert();
});

// 页面打开时加载实时汇率
loadRates();
