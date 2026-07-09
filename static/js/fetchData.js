/**
 * Optimized AJAX Table & List Utility
 * Refactored to support both standard HTML table/tbody and custom div/flex-table layouts
 */
const tableAjaxConfigs = {};
const tableAbortControllers = {};
const tableEventListeners = {}; // Track listeners for cleanup

// Allowed HTTP methods
const ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'];

// --- Utility ---
const debounceTable = (fn, delay = 300) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
};

/**
 * Collect form data or use direct parameters from a form or wrapper container
 * @param {HTMLElement|string|null} formOrId - Form element, container element, ID, or null
 * @param {Object} defaultParams - Default parameters to include
 * @param {HTMLElement} table - Table/container element for sort data
 * @returns {URLSearchParams}
 */
const collectFormData = (formOrId, defaultParams = {}, table = null) => {
    const params = new URLSearchParams();

    let container = null;
    if (typeof formOrId === 'string') {
        container = document.getElementById(formOrId);
    } else if (formOrId instanceof HTMLElement) {
        container = formOrId;
    }

    // Collect data from any input/select/textarea under the container
    if (container) {
        container.querySelectorAll("input, select, textarea").forEach(input => {
            if (input.name && input.value.trim() !== "") {
                if (input.type === 'radio' && !input.checked) return;
                if (input.type === 'checkbox' && !input.checked) return;

                params.append(input.name, input.value.trim());

                // Integration with dropdown_style.js custom date range
                if (input.tagName === 'SELECT' && input.value === 'custom') {
                    const fromDate = input.getAttribute('data-from-date');
                    const toDate = input.getAttribute('data-to-date');
                    if (fromDate) params.append('from_date', fromDate);
                    if (toDate) params.append('to_date', toDate);
                }
            }
        });
    }

    // Add default parameters
    Object.entries(defaultParams).forEach(([k, v]) => {
        if (v !== undefined && v !== null) {
            const strValue = String(v);
            if (strValue.trim() !== "" || v === false || v === 0) {
                params.set(k, strValue);
            }
        }
    });

    // Include table/container sort if provided
    if (table && table.dataset.sort) {
        params.append("sort", table.dataset.sort);
    }

    return params;
};

// --- Loading Spinner ---
function showTableLoading(table, text = "Loading...") {
    if (!table) return;
    table.style.opacity = "0.6";
    table.setAttribute("aria-busy", "true");
    let spinner = document.getElementById(`${table.id}-loading`);
    if (!spinner) {
        spinner = document.createElement("div");
        spinner.id = `${table.id}-loading`;
        spinner.className = "table-spinner";
        spinner.setAttribute("role", "status");
        spinner.setAttribute("aria-live", "polite");
        spinner.setAttribute("aria-atomic", "true");
        spinner.innerHTML = `<i class="fas fa-spinner fa-spin" aria-hidden="true"></i><span>${text}</span>`;
        (table.closest('.table-container') || table.parentElement).appendChild(spinner);
    }
    spinner.style.display = "flex";
}

function hideTableLoading(table) {
    if (!table) return;
    table.style.opacity = "1";
    table.setAttribute("aria-busy", "false");
    const spinner = document.getElementById(`${table.id}-loading`);
    if (spinner) spinner.style.display = "none";
}

/**
 * Fetch with timeout wrapper
 * @param {string} url - URL to fetch
 * @param {Object} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Response>}
 */
async function fetchWithTimeout(url, options = {}, timeout = 30000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: options.signal ?
                AbortSignal.any([options.signal, controller.signal]) :
                controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError' && !options.signal?.aborted) {
            throw new Error('Request timeout');
        }
        throw error;
    }
}

// --- Core Table/List Loader ---
async function loadTableData(formId, tableId, fetchUrl, options = {}, page = 1) {
    const form = formId ? document.getElementById(formId) : null;
    const table = document.getElementById(tableId);
    if (!table || !fetchUrl) return false;

    // Detect if it is a standard table or custom flex-based container
    const tableBody = table.querySelector("tbody");
    const isStandardTable = table.tagName === 'TABLE' || tableBody !== null;
    const targetElement = isStandardTable ? tableBody : table;

    const paginationId = `${tableId}_pagination`;
    let paginationWrapper = document.getElementById(paginationId);
    
    // Setup pagination wrapper if not inline and doesn't exist yet
    if (!options.inlinePagination && !paginationWrapper) {
        paginationWrapper = document.createElement("div");
        paginationWrapper.id = paginationId;
        paginationWrapper.className = "pagination-wrapper";
        paginationWrapper.style.display = "none";
        if (isStandardTable) {
            (table.closest(".table-container") || table.parentElement).appendChild(paginationWrapper);
        } else {
            table.parentNode.insertBefore(paginationWrapper, table.nextSibling);
        }
    }

    // Cancel any running request
    tableAbortControllers[tableId]?.abort();
    const abortController = new AbortController();
    tableAbortControllers[tableId] = abortController;

    // Show loading state
    if (isStandardTable) {
        const cols = table.querySelector("thead tr")?.children.length || 1;
        const loadingText = options.loadingText || "Loading...";
        targetElement.innerHTML = `
            <tr>
                <td colspan="${cols}" class="text-center loading-cell" role="status" aria-live="polite">
                    <div class="loading">
                        <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
                        ${loadingText}
                    </div>
                </td>
            </tr>
        `;
    } else {
        const loadingText = options.loadingText || "Loading...";
        targetElement.innerHTML = `
            <div class="loader-placeholder">
                <span class="loader-spinner"></span>
                <p style="margin-top: 8px;">${loadingText}</p>
            </div>
        `;
    }

    try {
        const params = collectFormData(formId, options.defaultParams || {}, table);
        params.append("page", page);

        const method = (options.method?.toUpperCase() || "GET");
        if (!ALLOWED_METHODS.includes(method)) {
            throw new Error(`Invalid HTTP method: ${method}`);
        }

        const req = {
            method,
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: abortController.signal
        };
        const url = method === "POST" ? fetchUrl : `${fetchUrl}?${params}`;
        if (method === "POST") {
            req.body = params;
            req.headers["Content-Type"] = "application/x-www-form-urlencoded";
        }

        const timeout = options.timeout || 30000;
        const res = await fetchWithTimeout(url, req, timeout);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        if (!data.success) throw new Error("Backend error");

        const htmlContent = data.html || "";
        if (typeof htmlContent !== 'string') {
            throw new Error("Invalid HTML content received");
        }

        // Replace content
        if (isStandardTable) {
            targetElement.innerHTML = htmlContent;
            if (paginationWrapper) {
                updatePagination(paginationWrapper, data.pagination, (page) =>
                    loadTableData(formId, tableId, fetchUrl, options, page)
                );
            }
        } else {
            if (options.inlinePagination) {
                targetElement.innerHTML = htmlContent + (data.pagination || "");
                bindContainerPagination(targetElement, (page) =>
                    loadTableData(formId, tableId, fetchUrl, options, page)
                );
            } else {
                targetElement.innerHTML = htmlContent;
                if (paginationWrapper) {
                    updatePagination(paginationWrapper, data.pagination, (page) =>
                        loadTableData(formId, tableId, fetchUrl, options, page)
                    );
                }
            }
        }

        // Focus management
        const activeElement = document.activeElement;
        const isUserTyping = activeElement && (
            activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.tagName === 'SELECT'
        );

        const firstFocusable = targetElement.querySelector('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (firstFocusable && options.focusAfterLoad !== false && !isUserTyping) {
            firstFocusable.focus();
        }

        // Highlight active sorting columns
        const sortString = table.dataset.sort || "";
        const currentSorts = sortString.split(',').filter(s => s.trim());
        table.querySelectorAll("[data-sort]").forEach(header => {
            const field = header.getAttribute("data-sort");
            const sortItem = currentSorts.find(s => s === field || s === `-${field}`);
            if (sortItem) {
                header.classList.add("active-sort");
                header.style.color = "var(--accent-primary)";
            } else {
                header.classList.remove("active-sort");
                header.style.color = "";
            }
        });

        table.dispatchEvent(new CustomEvent("tableDataLoaded", { detail: { data } }));
        options.onSuccess?.(data, table);
        return true;
    } catch (err) {
        if (err.name === "AbortError") return false;
        console.error("Table Load Error:", err);
        showTableError(table, err, options, formId, tableId, fetchUrl, isStandardTable);
        options.onError?.(err, table);
        return false;
    }
}

// --- Helpers ---
function showTableError(table, error, options, formId, tableId, fetchUrl, isStandardTable) {
    const errorText = options.errorText || "Error loading data.";
    const retryText = options.retryText || "Retry";

    if (isStandardTable) {
        const tbody = table.querySelector("tbody");
        const cols = table.querySelector("thead tr")?.children.length || 1;
        tbody.innerHTML = `
            <tr>
                <td colspan="${cols}" class="text-center" role="alert">
                    ${errorText}
                    <button class="btn btn-sm btn-outline-primary retry-btn" aria-label="${retryText}">${retryText}</button>
                </td>
            </tr>
        `;
        const retryBtn = tbody.querySelector(".retry-btn");
        if (retryBtn) {
            const listener = () => loadTableData(formId, tableId, fetchUrl, options);
            retryBtn.addEventListener("click", listener);
            if (!tableEventListeners[tableId]) tableEventListeners[tableId] = [];
            tableEventListeners[tableId].push({ element: retryBtn, event: 'click', handler: listener });
        }
    } else {
        table.innerHTML = `
            <div class="glass-panel" style="padding: 48px; text-align: center; color: var(--error);">
                <div style="font-size: 24px; margin-bottom: 8px;">⚠️</div>
                <p>${errorText}</p>
                <button class="btn btn--secondary btn--sm retry-btn" style="margin-top: 12px;" aria-label="${retryText}">${retryText}</button>
            </div>
        `;
        const retryBtn = table.querySelector(".retry-btn");
        if (retryBtn) {
            const listener = () => loadTableData(formId, tableId, fetchUrl, options);
            retryBtn.addEventListener("click", listener);
            if (!tableEventListeners[tableId]) tableEventListeners[tableId] = [];
            tableEventListeners[tableId].push({ element: retryBtn, event: 'click', handler: listener });
        }
    }
}

function updatePagination(wrapper, html, onClick) {
    if (!wrapper) return;
    if (!html || !html.trim()) {
        wrapper.innerHTML = "";
        wrapper.style.display = "none";
        return;
    }
    wrapper.style.display = "flex";
    wrapper.innerHTML = html;

    if (wrapper._paginationClickHandler) {
        wrapper.removeEventListener("click", wrapper._paginationClickHandler);
    }

    wrapper._paginationClickHandler = e => {
        const link = e.target.closest("[data-page]");
        if (!link) return;
        
        if (link.disabled || link.hasAttribute("disabled") || link.classList.contains("pagination__btn--active")) {
            return;
        }

        e.preventDefault();
        const page = link.dataset.page;
        onClick(page);
    };

    wrapper.addEventListener("click", wrapper._paginationClickHandler);
}

function bindContainerPagination(container, onClick) {
    if (container._paginationClickHandler) {
        container.removeEventListener("click", container._paginationClickHandler);
    }
    
    container._paginationClickHandler = e => {
        const btn = e.target.closest("[data-page]");
        if (!btn || !container.contains(btn)) return;
        
        if (btn.disabled || btn.hasAttribute("disabled") || btn.classList.contains("pagination__btn--active")) {
            return;
        }
        
        e.preventDefault();
        const page = btn.dataset.page;
        onClick(page);
    };
    
    container.addEventListener("click", container._paginationClickHandler);
}

/**
 * Cleanup function to remove event listeners and abort controllers for a table/container
 * @param {string} tableId - Table/container ID to clean up
 */
function cleanupTable(tableId) {
    tableAbortControllers[tableId]?.abort();
    delete tableAbortControllers[tableId];

    if (tableEventListeners[tableId]) {
        tableEventListeners[tableId].forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        delete tableEventListeners[tableId];
    }

    const container = document.getElementById(tableId);
    if (container) {
        if (container._sortDelegatedHandler) {
            container.removeEventListener("click", container._sortDelegatedHandler);
            delete container._sortDelegatedHandler;
        }
        if (container._sortKeydownHandler) {
            container.removeEventListener("keydown", container._sortKeydownHandler);
            delete container._sortKeydownHandler;
        }
        if (container._paginationClickHandler) {
            container.removeEventListener("click", container._paginationClickHandler);
            delete container._paginationClickHandler;
        }
    }

    const paginationWrapper = document.getElementById(`${tableId}_pagination`);
    if (paginationWrapper && paginationWrapper._paginationClickHandler) {
        paginationWrapper.removeEventListener("click", paginationWrapper._paginationClickHandler);
        delete paginationWrapper._paginationClickHandler;
    }

    delete tableAjaxConfigs[tableId];
}

// --- Table Initialization ---
function initTableAjax(formId, tableId, url, options = {}, includeInputs = false) {
    cleanupTable(tableId);

    tableAjaxConfigs[tableId] = { formId, tableId, fetchUrl: url, options };

    const form = formId ? document.getElementById(formId) : null;
    if (form) {
        const submitHandler = e => {
            e.preventDefault();
            loadTableData(formId, tableId, url, options);
        };
        form.addEventListener("submit", submitHandler);

        if (!tableEventListeners[tableId]) {
            tableEventListeners[tableId] = [];
        }
        tableEventListeners[tableId].push({ element: form, event: 'submit', handler: submitHandler });

        const selector = includeInputs ? "input, select, textarea" : "select, textarea";
        form.querySelectorAll(selector).forEach(input => {
            const debouncedHandler = debounceTable(() =>
                loadTableData(formId, tableId, url, options), options.debounceDelay || 400);
            input.addEventListener("input", debouncedHandler);

            tableEventListeners[tableId].push({ element: input, event: 'input', handler: debouncedHandler });
        });
    }

    if (options.autoLoad !== false) {
        loadTableData(formId, tableId, url, options);
    }
}

function reloadTable(id) {
    const cfg = tableAjaxConfigs[id];
    if (cfg) loadTableData(cfg.formId, cfg.tableId, cfg.fetchUrl, cfg.options);
}

// --- Sorting via Event Delegation ---
function initTableSorting(id) {
    const container = document.getElementById(id);
    if (!container) return;

    if (container._sortDelegatedHandler) {
        container.removeEventListener("click", container._sortDelegatedHandler);
    }

    const clickHandler = (e) => {
        const header = e.target.closest("[data-sort]");
        if (!header || !container.contains(header)) return;

        e.preventDefault();
        const field = header.dataset.sort;
        let currentSorts = (container.dataset.sort || "").split(',').filter(s => s.trim());

        const getSortState = (f) => {
            const match = currentSorts.find(s => s === f || s === `-${f}`);
            if (!match) return null;
            return match.startsWith('-') ? 'desc' : 'asc';
        };

        const state = getSortState(field);
        currentSorts = currentSorts.filter(s => s !== field && s !== `-${field}`);

        if (state === null) {
            currentSorts.push(field);
        } else if (state === 'asc') {
            currentSorts.push(`-${field}`);
        }

        container.dataset.sort = currentSorts.join(',');
        
        updateSortIndicators(container);
        reloadTable(id);
    };

    container._sortDelegatedHandler = clickHandler;
    container.addEventListener("click", clickHandler);

    if (container._sortKeydownHandler) {
        container.removeEventListener("keydown", container._sortKeydownHandler);
    }
    const keydownHandler = (e) => {
        const header = e.target.closest("[data-sort]");
        if (!header || !container.contains(header)) return;

        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            header.click();
        }
    };
    container._sortKeydownHandler = keydownHandler;
    container.addEventListener("keydown", keydownHandler);

    updateSortIndicators(container);
}

function updateSortIndicators(table) {
    const sortString = table.dataset.sort || "";
    const currentSorts = sortString.split(',').filter(s => s.trim());

    table.querySelectorAll("[data-sort]").forEach(th => {
        const field = th.dataset.sort;
        const sortItem = currentSorts.find(s => s === field || s === `-${field}`);

        th.classList.remove("asc", "desc");

        let badge = th.querySelector('.sort-priority');
        if (badge) badge.remove();

        let icon = th.querySelector('.sort-icon');
        if (icon && (icon.tagName === 'I' || icon.classList.contains('fas'))) {
            if (sortItem) {
                const isDesc = sortItem.startsWith('-');
                th.classList.add(isDesc ? "desc" : "asc");
                icon.className = isDesc ? 'fas fa-sort-down sort-icon' : 'fas fa-sort-up sort-icon';
                icon.style.opacity = '1';

                if (currentSorts.length > 1) {
                    const priority = currentSorts.indexOf(sortItem) + 1;
                    badge = document.createElement('span');
                    badge.className = 'sort-priority';
                    badge.innerText = priority;
                    badge.style.fontSize = '0.7em';
                    badge.style.verticalAlign = 'super';
                    badge.style.marginLeft = '2px';
                    th.appendChild(badge);
                }
            } else {
                icon.className = 'fas fa-sort sort-icon';
                icon.style.opacity = '0.3';
            }
        } else if (icon) {
            if (sortItem) {
                const isDesc = sortItem.startsWith('-');
                icon.textContent = isDesc ? '↓' : '↑';
            } else {
                icon.textContent = '↕';
            }
        }
    });
}

// --- PDF Download Helpers ---
function getTableQueryParams(formId, tableId, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return new URLSearchParams();
    return collectFormData(formId, options.defaultParams || {}, table);
}

function generatePDFUrl(formId, tableId, pdfBaseUrl, options = {}) {
    const params = getTableQueryParams(formId, tableId, options);
    return `${pdfBaseUrl}?${params.toString()}`;
}

function downloadTablePDF(formId, tableId, pdfBaseUrl, options = {}) {
    const pdfUrl = generatePDFUrl(formId, tableId, pdfBaseUrl, options);
    window.open(pdfUrl, '_blank');
}

// --- Extend $ wrapper with ajax method ---
(function () {
    const original$ = window.$;
    if (typeof original$ === 'function') {
        window.$ = function (selector) {
            const result = original$(selector);
            if (result && typeof result === 'object' && !Array.isArray(result)) {
                result.ajax = function (options = {}) {
                    const form = typeof selector === "string" ? document.querySelector(selector) : selector;
                    if (!form) {
                        console.error("Table AJAX: Element not found");
                        return this;
                    }
                    const config = {
                        tableId: options.tableId || "",
                        url: options.url || "",
                        placeholder: options.placeholder || "Loading...",
                        method: options.method || "GET",
                        debounceDelay: options.debounceDelay || 400,
                        includeInputs: options.includeInputs || false,
                        autoLoad: options.autoLoad !== false,
                        sortable: options.sortable !== false,
                        onSuccess: options.onSuccess || null,
                        onError: options.onError || null,
                        defaultParams: options.defaultParams || {},
                        inlinePagination: options.inlinePagination !== false,
                        ...options
                    };
                    if (!config.tableId || !config.url) {
                        console.error("Table AJAX: tableId and url are required");
                        return this;
                    }
                    initTableAjax(form.id, config.tableId, config.url, {
                        method: config.method,
                        debounceDelay: config.debounceDelay,
                        loadingText: config.placeholder,
                        autoLoad: config.autoLoad,
                        onSuccess: config.onSuccess,
                        onError: config.onError,
                        defaultParams: config.defaultParams,
                        inlinePagination: config.inlinePagination
                    }, config.includeInputs);
                    if (config.sortable) {
                        initTableSorting(config.tableId);
                    }
                    return this;
                };
            }
            return result;
        };
    }
})();

// --- Global expose ---
window.loadTableData = loadTableData;
window.initTableAjax = initTableAjax;
window.reloadTable = reloadTable;
window.initTableSorting = initTableSorting;
window.updateSortIndicators = updateSortIndicators;
window.getTableQueryParams = getTableQueryParams;
window.generatePDFUrl = generatePDFUrl;
window.downloadTablePDF = downloadTablePDF;
window.cleanupTable = cleanupTable;
