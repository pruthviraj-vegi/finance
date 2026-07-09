document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("categorySearch");
  const tableContainer = document.getElementById("categoryTableContainer");

  let currentSearch = "";
  let currentSort = "name";
  let currentPage = 1;
  let debounceTimeout = null;

  // Initial data load
  fetchData();

  // Search input change with debounce
  if (searchInput) {
    searchInput.addEventListener("input", function (e) {
      currentSearch = e.target.value.trim();
      currentPage = 1; // Reset to page 1 on new search

      clearTimeout(debounceTimeout);
      debounceTimeout = setTimeout(fetchData, 300);
    });
  }

  // Fetch the data from server AJAX endpoint
  function fetchData() {
    const tableBody = tableContainer.querySelector(".category-list");
    if (tableBody) {
      tableBody.style.opacity = "0.5";
    }

    const queryUrl = `/expense/categories/fetch/?search=${encodeURIComponent(currentSearch)}&sort=${currentSort}&page=${currentPage}`;

    fetch(queryUrl, {
      headers: {
        "X-Requested-With": "XMLHttpRequest"
      }
    })
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          tableContainer.innerHTML = data.html + data.pagination;
          bindSortableHeaders();
          bindPaginationButtons();
        } else {
          showError("Failed to load categories.");
        }
      })
      .catch(error => {
        console.error("Fetch error:", error);
        showError("An error occurred while loading categories.");
      });
  }

  // Bind sorting controls to headers
  function bindSortableHeaders() {
    const headers = tableContainer.querySelectorAll(".sortable");
    headers.forEach(header => {
      const field = header.getAttribute("data-sort");
      
      if (currentSort === field || currentSort === `-${field}`) {
        header.style.color = "var(--accent-primary)";
      }

      header.addEventListener("click", function () {
        if (currentSort === field) {
          currentSort = `-${field}`;
        } else {
          currentSort = field;
        }
        currentPage = 1;
        fetchData();
      });
    });
  }

  // Bind pagination page buttons
  function bindPaginationButtons() {
    const buttons = tableContainer.querySelectorAll(".pagination__btn");
    buttons.forEach(btn => {
      btn.addEventListener("click", function () {
        if (btn.disabled || btn.classList.contains("pagination__btn--active")) {
          return;
        }
        const targetPage = parseInt(btn.getAttribute("data-page"), 10);
        if (targetPage) {
          currentPage = targetPage;
          fetchData();
        }
      });
    });
  }

  // Helper to show error status in container
  function showError(msg) {
    tableContainer.innerHTML = `
      <div class="glass-panel" style="padding: 48px; text-align: center; color: var(--error);">
        <div style="font-size: 24px; margin-bottom: 8px;">⚠️</div>
        <p>${msg}</p>
        <button class="btn btn--secondary btn--sm" style="margin-top: 12px;" onclick="location.reload()">Retry</button>
      </div>
    `;
  }
});
