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
});
