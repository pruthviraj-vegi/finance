document.addEventListener("DOMContentLoaded", function () {
  const grid = document.getElementById("recurringGrid");
  if (!grid) return;

  const cards = Array.from(grid.querySelectorAll(".dash-card[data-type]"));
  const addCard = grid.querySelector(".dash-card--add");

  // Calculate counts dynamically from rendered cards
  const counts = {
    all: cards.filter(c => c.getAttribute("data-type") !== "add").length,
    emi: cards.filter(c => c.getAttribute("data-type") === "emi").length,
    subscription: cards.filter(c => c.getAttribute("data-type") === "subscription").length,
    renewal: cards.filter(c => c.getAttribute("data-type") === "renewal").length,
  };

  // Update counts in pill badges
  document.querySelectorAll("#countAllPill").forEach(el => el.textContent = counts.all);
  document.querySelectorAll("#countEmiPill").forEach(el => el.textContent = counts.emi);
  document.querySelectorAll("#countSubPill").forEach(el => el.textContent = counts.subscription);
  document.querySelectorAll("#countRenPill").forEach(el => el.textContent = counts.renewal);

  let emptyState = document.getElementById("recurringEmptyState");

  function filterCards(filter) {
    // Update active class on all filter pill buttons
    document.querySelectorAll(".filter-pill[data-filter]").forEach(btn => {
      if (btn.getAttribute("data-filter") === filter) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    let visibleCount = 0;

    cards.forEach(card => {
      const type = card.getAttribute("data-type");
      if (type === "add") {
        card.style.display = "";
        return;
      }

      if (filter === "all" || type === filter) {
        card.style.display = "";
        visibleCount++;
      } else {
        card.style.display = "none";
      }
    });

    // Handle empty state if no matching items
    if (visibleCount === 0 && filter !== "all") {
      if (!emptyState) {
        emptyState = document.createElement("div");
        emptyState.id = "recurringEmptyState";
        emptyState.className = "glass-panel empty-state py-24 text-center grid-span-full";
        grid.insertBefore(emptyState, addCard);
      }
      const filterNames = {
        emi: "EMI",
        subscription: "Subscription",
        renewal: "Annual Renewal"
      };
      emptyState.innerHTML = `
        <div class="empty-state__icon text-24 mb-8">🔍</div>
        <p class="text-14 font-medium text-primary m-0">No ${filterNames[filter] || filter} items found</p>
        <p class="text-12 text-secondary mt-4 mb-0">Select another filter or add a new recurring item.</p>
      `;
      emptyState.style.display = "block";
    } else if (emptyState) {
      emptyState.style.display = "none";
    }
  }

  // Event Delegation for filter clicks (pills, breakdown bar, legend)
  document.addEventListener("click", function (e) {
    const trigger = e.target.closest("[data-filter]");
    if (!trigger) return;

    const filter = trigger.getAttribute("data-filter");
    if (filter) {
      filterCards(filter);

      // If clicked from legend/breakdown at bottom, smooth scroll to grid
      if (trigger.classList.contains("legend-row__item") || trigger.classList.contains("breakdown-bar__seg")) {
        grid.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  });
});
