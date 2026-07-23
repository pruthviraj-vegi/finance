document.addEventListener('DOMContentLoaded', () => {
    // Micro-interactions for glass panels (mouse move tracking)
    document.querySelectorAll('.glass-panel').forEach(panel => {
        panel.addEventListener('mousemove', (e) => {
            const rect = panel.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            panel.style.setProperty('--mouse-x', `${x}px`);
            panel.style.setProperty('--mouse-y', `${y}px`);
        });
    });

    // Simple progress ring animation on load
    document.querySelectorAll('.progress-ring-circle').forEach(ring => {
        const finalOffset = ring.getAttribute('stroke-dashoffset');
        ring.style.strokeDashoffset = '125.6';
        setTimeout(() => {
            ring.style.strokeDashoffset = finalOffset;
        }, 100);
    });

    // Chart Data handling
    const chartDataEl = document.getElementById('chart-data');
    if (chartDataEl) {
        const chartData = JSON.parse(chartDataEl.textContent);

        function drawTrend(period) {
            let count = 6;
            if (period === '1M') count = 3;
            else if (period === '6M') count = 6;
            else if (period === '1Y') count = 12;

            const labels = chartData.labels.slice(-count);
            const income = chartData.income.slice(-count);
            const expense = chartData.expense.slice(-count);
            const netFlow = income.map((inc, i) => inc - expense[i]);

            // Find the max and min of netFlow to scale it properly
            let maxVal = Math.max(...netFlow, 100); // at least 100 to avoid division by zero
            let minVal = Math.min(...netFlow, 0); // include 0 to show baseline

            const range = maxVal - minVal;

            const points = [];
            const width = 800;
            const height = 160;
            const paddingBottom = 20;
            const paddingTop = 20;
            const graphHeight = height - paddingBottom - paddingTop;

            for (let i = 0; i < netFlow.length; i++) {
                // To avoid division by zero if count is 1
                const x = netFlow.length > 1 ? (i / (netFlow.length - 1)) * width : width / 2;
                // scale to graphHeight
                const normalized = range > 0 ? (netFlow[i] - minVal) / range : 0.5;
                const y = height - paddingBottom - (normalized * graphHeight);
                points.push({ x, y });
            }

            // Build SVG Path using Bezier curve interpolation
            let trendPath = "";
            if (points.length > 0) {
                trendPath = `M ${points[0].x} ${points[0].y}`;
                for (let i = 0; i < points.length - 1; i++) {
                    const p0 = points[i];
                    const p1 = points[i+1];
                    const cpX1 = p0.x + (p1.x - p0.x) / 2;
                    const cpY1 = p0.y;
                    const cpX2 = p0.x + (p1.x - p0.x) / 2;
                    const cpY2 = p1.y;
                    trendPath += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${p1.x} ${p1.y}`;
                }
            }

            const areaPath = trendPath ? `${trendPath} L ${width} ${height} L 0 ${height} Z` : "";

            const trendLineEl = document.getElementById('chartTrendLine');
            const areaPathEl = document.getElementById('chartAreaPath');
            
            if (trendLineEl && areaPathEl) {
                trendLineEl.setAttribute('d', trendPath);
                // Reset SVG line drawing animation
                trendLineEl.style.animation = 'none';
                trendLineEl.offsetHeight; // trigger reflow
                trendLineEl.style.animation = 'drawLine 1.5s forwards ease-in-out';
                
                areaPathEl.setAttribute('d', areaPath);
            }

            // Render labels
            const labelContainer = document.getElementById('chartLabels');
            if (labelContainer) {
                labelContainer.innerHTML = '';
                labels.forEach(label => {
                    const span = document.createElement('span');
                    span.textContent = label;
                    labelContainer.appendChild(span);
                });
            }
        }

        // Draw initial 6M trend
        drawTrend('6M');

        // Setup period button handlers
        const buttons = document.querySelectorAll('[data-period]');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => {
                    b.classList.remove('bg-accent-primary', 'text-on-primary');
                    b.classList.add('bg-glass-fill-dark', 'text-on-surface-variant');
                });
                
                btn.classList.remove('bg-glass-fill-dark', 'text-on-surface-variant');
                btn.classList.add('bg-accent-primary', 'text-on-primary');

                const period = btn.getAttribute('data-period');
                drawTrend(period);
            });
        });
    }

    // Category Breakdown interactive highlight on click
    setupCategoryBreakdown();
});

function setupCategoryBreakdown() {
    const segments = document.querySelectorAll('.category-segment');
    const legendItems = document.querySelectorAll('.category-breakdown-legend-item');
    const centerVal = document.getElementById('donutCenterVal');
    const centerLbl = document.getElementById('donutCenterLbl');
    const centerContainer = document.getElementById('donutCenter');

    if (!centerVal || !centerLbl) return;

    const defaultVal = centerVal.getAttribute('data-default-val') || centerVal.textContent;
    const defaultLbl = centerLbl.getAttribute('data-default-lbl') || centerLbl.textContent;

    let activeCategory = null;

    function selectCategory(name, amount, pct, color) {
        if (activeCategory === name) {
            resetCategorySelection();
            return;
        }

        activeCategory = name;

        // Highlight center text with category amount and percentage (no category name)
        centerVal.textContent = amount;
        centerLbl.textContent = `${pct}%`;
        centerLbl.setAttribute('title', `${name}: ${amount} (${pct}%)`);
        centerVal.style.color = color || 'var(--accent-primary)';

        // Adjust font size dynamically if amount string is long
        if (amount.length > 9) {
            centerVal.style.fontSize = '0.78rem';
        } else if (amount.length > 7) {
            centerVal.style.fontSize = '0.84rem';
        } else {
            centerVal.style.fontSize = '0.9375rem';
        }

        // Highlight SVG path segment
        segments.forEach(path => {
            const pathName = path.getAttribute('data-name');
            const pathColor = path.getAttribute('data-color');
            if (pathName === name) {
                path.style.opacity = '1';
                path.style.strokeWidth = '4';
                path.style.filter = `drop-shadow(0 0 3px ${pathColor})`;
            } else {
                path.style.opacity = '0.25';
                path.style.strokeWidth = '2.5';
                path.style.filter = 'none';
            }
        });

        // Highlight legend item
        legendItems.forEach(item => {
            const itemName = item.getAttribute('data-name');
            if (itemName === name) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    function resetCategorySelection() {
        activeCategory = null;
        centerVal.textContent = defaultVal;
        centerLbl.textContent = defaultLbl;
        centerVal.style.color = 'var(--text-primary)';
        centerVal.style.fontSize = '0.875rem';

        segments.forEach(path => {
            const pathColor = path.getAttribute('data-color');
            path.style.opacity = '0.9';
            path.style.strokeWidth = '3';
            path.style.filter = pathColor ? `drop-shadow(0 0 3px ${pathColor})` : 'none';
        });

        legendItems.forEach(item => {
            item.classList.remove('active');
        });
    }

    // Donut SVG path click listeners
    segments.forEach(path => {
        path.addEventListener('click', (e) => {
            e.stopPropagation();
            const name = path.getAttribute('data-name');
            const amount = path.getAttribute('data-amount');
            const pct = path.getAttribute('data-percentage');
            const color = path.getAttribute('data-color');
            selectCategory(name, amount, pct, color);
        });
    });

    // Legend item click listeners
    legendItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const name = item.getAttribute('data-name');
            const amount = item.getAttribute('data-amount');
            const pct = item.getAttribute('data-percentage');
            const color = item.getAttribute('data-color');
            selectCategory(name, amount, pct, color);
        });
    });

    // Click center to reset to total
    if (centerContainer) {
        centerContainer.addEventListener('click', (e) => {
            e.stopPropagation();
            resetCategorySelection();
        });
    }
}
