/* ============================================
   Vault Glass — Dashboard Logic
   Random sample data, easy to replace with API calls later.
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  initSidebar();
  initAlerts();
  initDateDisplay();
  initDashboardData();
  initChartPeriodToggle();
  initRevenueChart();
  initIndianNumberInputs();
  initFlatpickr();
  initAutofocus();
});

/* ============================================
   Sidebar Toggle (Mobile)
   ============================================ */
function initSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggle = document.getElementById('sidebarToggle');
  const close = document.getElementById('sidebarClose');
  const collapseBtn = document.getElementById('sidebarCollapseBtn');
  if (!sidebar) return;

  function openSidebar() { sidebar.classList.add('open'); overlay.classList.add('active'); }
  function closeSidebar() { sidebar.classList.remove('open'); overlay.classList.remove('active'); }

  if (toggle) toggle.addEventListener('click', openSidebar);
  if (close) close.addEventListener('click', closeSidebar);
  if (overlay) overlay.addEventListener('click', closeSidebar);

  // Desktop Collapse Toggle logic
  if (collapseBtn) {
    // Restore state from localStorage
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
      document.body.classList.add('sidebar-collapsed');
    }

    collapseBtn.addEventListener('click', () => {
      const currentlyCollapsed = document.body.classList.toggle('sidebar-collapsed');
      localStorage.setItem('sidebar-collapsed', currentlyCollapsed);
    });
  }
}

/* ============================================
   Alert Dismiss
   ============================================ */
function initAlerts() {
  document.querySelectorAll('.alert__close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-8px)';
      setTimeout(() => alert.remove(), 300);
    });
  });
}

/* ============================================
   Date Display
   ============================================ */
function initDateDisplay() {
  const dayEl = document.getElementById('currentDay');
  const dateEl = document.getElementById('currentDate');
  if (!dayEl || !dateEl) return;
  const now = new Date();
  const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  dayEl.textContent = days[now.getDay()];
  dateEl.textContent = `${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`;
}

/* ============================================
   Dashboard Sample Data
   Replace these functions with API calls later:
     fetch('/api/dashboard/stats/').then(r => r.json()).then(data => updateStats(data));
   ============================================ */
function initDashboardData() {
  if (document.getElementById('live-dashboard-marker')) return;
  // Generate random but realistic financial data
  const data = generateSampleData();
  updateStats(data);
  renderTransactions(data.transactions);
  renderCategories(data.categories);
}

function generateSampleData() {
  const income = randomBetween(180000, 350000);
  const expense = randomBetween(80000, income * 0.7);
  const balance = income - expense;
  const pendingCount = randomBetween(3, 12);
  const pendingAmount = randomBetween(15000, 80000);

  const categories = [
    { name: 'Rent & Utilities', amount: randomBetween(15000, 35000), color: '#7C9CFF' },
    { name: 'Salaries', amount: randomBetween(40000, 90000), color: '#34D399' },
    { name: 'Office Supplies', amount: randomBetween(5000, 15000), color: '#FB7185' },
    { name: 'Marketing', amount: randomBetween(8000, 25000), color: '#FBBF24' },
    { name: 'Transport', amount: randomBetween(3000, 12000), color: '#B4C5FF' },
  ].sort((a, b) => b.amount - a.amount);

  const txnNames = [
    { name: 'Client Payment - Acme Corp', cat: 'Invoice', type: 'income' },
    { name: 'Office Rent - July', cat: 'Rent', type: 'expense' },
    { name: 'Freelance Design Project', cat: 'Services', type: 'income' },
    { name: 'AWS Cloud Hosting', cat: 'Technology', type: 'expense' },
    { name: 'Staff Salary - Q2', cat: 'Salaries', type: 'expense' },
    { name: 'Product Sales - Batch #47', cat: 'Sales', type: 'income' },
    { name: 'Google Ads Campaign', cat: 'Marketing', type: 'expense' },
    { name: 'Consulting Fee - XYZ Ltd', cat: 'Services', type: 'income' },
    { name: 'Electricity Bill', cat: 'Utilities', type: 'expense' },
    { name: 'Equipment Purchase', cat: 'Assets', type: 'expense' },
  ];

  const transactions = txnNames.map((t, i) => ({
    ...t,
    amount: t.type === 'income' ? randomBetween(10000, 80000) : randomBetween(2000, 40000),
    date: daysAgo(i),
  }));

  return {
    income, expense, balance, pendingCount, pendingAmount,
    incomeTrend: randomBetween(5, 25),
    expenseTrend: randomBetween(2, 15),
    balanceTrend: randomBetween(8, 30),
    categories, transactions
  };
}

/* Update stat cards — call this with real API data later */
function updateStats(data) {
  setText('totalIncome', formatCurrency(data.income));
  setText('totalExpense', formatCurrency(data.expense));
  setText('netBalance', formatCurrency(data.balance));
  setText('pendingCount', data.pendingCount);
  setText('incomeTrend', `+${data.incomeTrend}%`);
  setText('expenseTrend', `-${data.expenseTrend}%`);
  setText('balanceTrend', `+${data.balanceTrend}%`);
  setText('pendingAmount', `${formatCurrency(data.pendingAmount)} total pending`);
  animateCounters();
}

function renderTransactions(transactions) {
  const list = document.getElementById('transactionsList');
  if (!list) return;
  list.innerHTML = transactions.map(t => `
    <div class="txn-item">
      <div class="txn-icon txn-icon--${t.type}">
        ${t.type === 'income' ? '↑' : '↓'}
      </div>
      <div class="txn-details">
        <div class="txn-name">${t.name}</div>
        <div class="txn-category">${t.cat}</div>
      </div>
      <div>
        <div class="txn-amount txn-amount--${t.type}">
          ${t.type === 'income' ? '+' : '-'}${formatCurrency(t.amount)}
        </div>
        <div class="txn-date">${t.date}</div>
      </div>
    </div>
  `).join('');
}

function renderCategories(categories) {
  const list = document.getElementById('categoriesList');
  if (!list) return;
  const max = categories[0].amount;
  list.innerHTML = categories.map(c => `
    <div class="category-item">
      <div class="category-dot" style="background:${c.color}"></div>
      <div class="category-info">
        <div class="category-name">
          <span>${c.name}</span>
          <span style="color:var(--text-muted);font-family:var(--font-mono);font-size:12px">${formatCurrency(c.amount)}</span>
        </div>
        <div class="category-bar">
          <div class="category-bar__fill" style="width:0%;background:${c.color}" data-width="${(c.amount / max * 100).toFixed(0)}%"></div>
        </div>
      </div>
    </div>
  `).join('');
  // Animate bars after render
  requestAnimationFrame(() => {
    document.querySelectorAll('.category-bar__fill').forEach(bar => {
      bar.style.width = bar.dataset.width;
    });
  });
}

/* ============================================
   Simple Bar Chart (Canvas)
   ============================================ */
function initRevenueChart() {
  if (document.getElementById('live-dashboard-marker')) return;
  const canvas = document.getElementById('revenueCanvas');
  if (!canvas) return;
  drawRevenueChart(canvas, 'week');
}

function drawRevenueChart(canvas, period) {
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.parentElement.getBoundingClientRect();
  canvas.width = rect.width * dpr;
  canvas.height = rect.height * dpr;
  ctx.scale(dpr, dpr);
  const W = rect.width, H = rect.height;

  let labels, incomeData, expenseData;
  if (period === 'week') {
    labels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
    incomeData = labels.map(() => randomBetween(8000, 45000));
    expenseData = labels.map(() => randomBetween(3000, 25000));
  } else if (period === 'month') {
    labels = ['W1','W2','W3','W4'];
    incomeData = labels.map(() => randomBetween(40000, 120000));
    expenseData = labels.map(() => randomBetween(20000, 80000));
  } else {
    labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    incomeData = labels.map(() => randomBetween(100000, 350000));
    expenseData = labels.map(() => randomBetween(60000, 200000));
  }

  const allValues = [...incomeData, ...expenseData];
  const maxVal = Math.max(...allValues) * 1.15;
  const padL = 60, padR = 20, padT = 20, padB = 40;
  const chartW = W - padL - padR, chartH = H - padT - padB;
  const barGroupW = chartW / labels.length;
  const barW = barGroupW * 0.3;

  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = padT + (chartH / 4) * i;
    ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
    ctx.fillStyle = '#6B7280'; ctx.font = '11px Inter, sans-serif'; ctx.textAlign = 'right';
    ctx.fillText(formatShort(maxVal - (maxVal / 4) * i), padL - 8, y + 4);
  }

  // Bars
  labels.forEach((label, i) => {
    const x = padL + barGroupW * i + barGroupW * 0.15;
    const incH = (incomeData[i] / maxVal) * chartH;
    const expH = (expenseData[i] / maxVal) * chartH;
    // Income bar
    const grad1 = ctx.createLinearGradient(0, padT + chartH - incH, 0, padT + chartH);
    grad1.addColorStop(0, 'rgba(52,211,153,0.8)'); grad1.addColorStop(1, 'rgba(52,211,153,0.3)');
    ctx.fillStyle = grad1;
    roundRect(ctx, x, padT + chartH - incH, barW, incH, 4);
    // Expense bar
    const grad2 = ctx.createLinearGradient(0, padT + chartH - expH, 0, padT + chartH);
    grad2.addColorStop(0, 'rgba(251,113,133,0.8)'); grad2.addColorStop(1, 'rgba(251,113,133,0.3)');
    ctx.fillStyle = grad2;
    roundRect(ctx, x + barW + 4, padT + chartH - expH, barW, expH, 4);
    // Label
    ctx.fillStyle = '#6B7280'; ctx.font = '11px Inter, sans-serif'; ctx.textAlign = 'center';
    ctx.fillText(label, x + barW + 2, H - 12);
  });

  // Legend
  ctx.fillStyle = 'rgba(52,211,153,0.8)';
  ctx.fillRect(W - 160, 8, 10, 10);
  ctx.fillStyle = '#9AA3B2'; ctx.font = '11px Inter'; ctx.textAlign = 'left';
  ctx.fillText('Income', W - 146, 17);
  ctx.fillStyle = 'rgba(251,113,133,0.8)';
  ctx.fillRect(W - 82, 8, 10, 10);
  ctx.fillStyle = '#9AA3B2';
  ctx.fillText('Expense', W - 68, 17);
}

function roundRect(ctx, x, y, w, h, r) {
  if (h <= 0) return;
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h);
  ctx.lineTo(x, y + h); ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y); ctx.fill();
}

function initChartPeriodToggle() {
  document.querySelectorAll('.chip[data-period]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.chip[data-period]').forEach(c => c.classList.remove('chip--active'));
      chip.classList.add('chip--active');
      const canvas = document.getElementById('revenueCanvas');
      if (canvas) drawRevenueChart(canvas, chip.dataset.period);
    });
  });
}

/* ============================================
   Counter Animation
   ============================================ */
function animateCounters() {
  document.querySelectorAll('.stat-card__value:not(.no-anim)').forEach(el => {
    const text = el.textContent;
    const match = text.replace(/[^0-9.]/g, '');
    if (!match) return;
    const target = parseFloat(match);
    const prefix = text.replace(match, '').replace(/[0-9.,]/g, '').trim().split('').shift() || '';
    let current = 0;
    const duration = 1200;
    const start = performance.now();
    function tick(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      current = target * eased;
      if (target > 999) {
        el.textContent = `₹${Math.floor(current).toLocaleString('en-IN')}`;
      } else {
        el.textContent = Math.floor(current).toString();
      }
      if (progress < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

/* ============================================
   Helpers
   ============================================ */
function randomBetween(min, max) { return Math.floor(Math.random() * (max - min + 1)) + min; }
function formatCurrency(n) { return '₹' + n.toLocaleString('en-IN'); }
function formatShort(n) { return n >= 100000 ? (n/100000).toFixed(1)+'L' : n >= 1000 ? (n/1000).toFixed(0)+'K' : n.toString(); }
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function daysAgo(d) {
  const dt = new Date(); dt.setDate(dt.getDate() - d);
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${dt.getDate()} ${months[dt.getMonth()]}`;
}

/* Resize chart on window resize */
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    const canvas = document.getElementById('revenueCanvas');
    const active = document.querySelector('.chip--active[data-period]');
    if (canvas && active) drawRevenueChart(canvas, active.dataset.period);
  }, 250);
});

/* ============================================
   Input Formatting
   ============================================ */
function formatIndianNumber(value, maxDecimals = 2) {
    if (value === undefined || value === null) {
        return '';
    }
    value = String(value);

    // Check if negative
    let isNegative = value.indexOf('-') === 0;

    // Remove all non-numeric except decimal point
    value = value.replace(/[^\d.]/g, '');
    
    // Allow only one decimal point
    const decimalCount = (value.match(/\./g) || []).length;
    if (decimalCount > 1) {
        const firstDecimalIndex = value.indexOf('.');
        value = value.slice(0, firstDecimalIndex + 1) + 
                value.slice(firstDecimalIndex + 1).replace(/\./g, '');
    }
    
    // Split integer and decimal
    let [intPart, decPart] = value.split('.');
    
    // Format integer part (Indian style)
    if (intPart && intPart.length > 0) {
        // Remove leading zeros
        intPart = intPart.replace(/^0+/, '');
        if (!intPart && decPart === undefined) {
            intPart = '0';
        } else if (!intPart) {
            intPart = '0';
        }
        
        if (intPart.length > 3) {
            let last3 = intPart.slice(-3);
            let others = intPart.slice(0, -3);
            intPart = others.replace(/\B(?=(\d{2})+(?!\d))/g, ',') + ',' + last3;
        }
    }
    
    let result = intPart;

    // Limit decimal places
    if (decPart !== undefined) {
        decPart = decPart.slice(0, maxDecimals);
        result = intPart + '.' + decPart;
    } else if (value.endsWith('.')) {
        // If user is typing decimal point
        result = intPart + '.';
    }

    if (isNegative && result && result !== '0') {
        return '-' + result;
    } else if (isNegative) {
        return '-';
    }
    
    return result || '';
}

function initIndianNumberInputs() {
    // Apply to all .indian-number inputs
    document.querySelectorAll('.indian-number').forEach(input => {
        const maxDecimals = parseInt(input.dataset.decimals) || 2;
        
        // Format initial value if present
        if (input.value) {
            input.value = formatIndianNumber(input.value, maxDecimals);
        }
        
        input.addEventListener('input', function(e) {
            const cursorPos = e.target.selectionStart;
            const oldLength = e.target.value.length;
            
            const formatted = formatIndianNumber(e.target.value, maxDecimals);
            e.target.value = formatted;
            
            // Adjust cursor position
            const newLength = formatted.length;
            const diff = newLength - oldLength;
            e.target.setSelectionRange(cursorPos + diff, cursorPos + diff);
        });
        
        // Clean up on blur
        input.addEventListener('blur', function(e) {
            let value = e.target.value;
            
            // Remove trailing decimal point
            if (value.endsWith('.')) {
                value = value.slice(0, -1);
            }
            
            // Add .00 if no decimal for money fields
            if (maxDecimals > 0 && !value.includes('.') && value !== '') {
                value += '.00';
            }
            
            e.target.value = value;
        });
    });

    // Remove commas before form submission so backend can parse the numeric values
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            form.querySelectorAll('.indian-number').forEach(input => {
                input.value = input.value.replace(/,/g, '');
            });
        });
    });
}

/* ============================================
   Flatpickr Global Initialization
   ============================================ */
function initFlatpickr() {
  if (typeof flatpickr !== 'undefined') {
    flatpickr('input[type="date"]', {
      altInput: true,
      altFormat: "d-m-Y",
      dateFormat: "Y-m-d",
      disableMobile: true // Ensure consistent themed style on mobile
    });
  }
}

/* ============================================
   Autofocus First Input on Load
   ============================================ */
function initAutofocus() {
  const pageContent = document.getElementById('pageContent') || document.querySelector('.page-content');
  if (!pageContent) return;

  // Disable auto-focus on mobile devices to prevent the virtual keyboard from popping up
  if (window.innerWidth <= 768) return;

  // Selectable input types: inputs (excluding button/hidden/submit etc), selects, textareas
  const focusableSelector = [
    'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([disabled]):not([readonly])',
    'select:not([disabled]):not([readonly])',
    'textarea:not([disabled]):not([readonly])'
  ].join(', ');

  const candidates = pageContent.querySelectorAll(focusableSelector);

  for (const el of candidates) {
    // Check if the element is visible in the viewport/layout
    const isVisible = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    if (isVisible) {
      el.focus();
      // For text-based inputs, position cursor at the end of the content
      if (el.tagName === 'INPUT' && ['text', 'search', 'url', 'tel', 'email', 'password', 'number'].includes(el.type)) {
        const len = el.value.length;
        el.setSelectionRange(len, len);
      }
      break;
    }
  }
}


