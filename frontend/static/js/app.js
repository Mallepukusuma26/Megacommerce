/**
 * MegaCommerce Web Application SPA Logic & REST Client
 * Zero External API Key Architecture
 */

let state = {
  authToken: localStorage.getItem("megacommerce_token") || null,
  currentUser: JSON.parse(localStorage.getItem("megacommerce_user") || "null"),
  cart: { items: [], grand_total: 0.0 }
};

document.addEventListener("DOMContentLoaded", () => {
  loadCategories();
  loadCatalog();
  updateAuthUI();
});

function switchPortal(portalName) {
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".portal-view").forEach(el => el.classList.remove("active"));

  if (portalName === "customer") {
    document.getElementById("customerPortal").classList.add("active");
    loadCatalog();
  } else if (portalName === "seller") {
    document.getElementById("sellerPortal").classList.add("active");
    loadSellerAnalytics();
  } else if (portalName === "admin") {
    document.getElementById("adminPortal").classList.add("active");
    loadAdminAnalytics();
  }
}

async function loadCategories() {
  try {
    const res = await fetch("/api/v1/catalog/categories");
    const json = await res.json();
    if (json.success) {
      const select = document.getElementById("categorySelect");
      select.innerHTML = '<option value="">All Categories</option>';
      json.data.forEach(cat => {
        const opt = document.createElement("option");
        opt.value = cat.id;
        opt.textContent = cat.name;
        select.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Failed to load categories:", err);
  }
}

async function loadCatalog() {
  try {
    const catId = document.getElementById("categorySelect")?.value || "";
    const sort = document.getElementById("sortSelect")?.value || "relevance";
    let url = `/api/v1/catalog/products?sort=${sort}`;
    if (catId) url += `&category_id=${catId}`;

    const res = await fetch(url);
    const json = await res.json();
    const grid = document.getElementById("productGrid");
    
    if (!json.data || json.data.length === 0) {
      grid.innerHTML = '<p style="color: var(--text-muted);">No products found in catalog.</p>';
      return;
    }

    grid.innerHTML = json.data.map(p => `
      <div class="card">
        <div>
          <span class="badge badge-info">$${p.price.toFixed(2)}</span>
          <h3 class="card-title" style="margin-top: 0.5rem;">${escapeHtml(p.title)}</h3>
          <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">Stock: ${p.stock_quantity} units</p>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-primary" style="flex: 1;" onclick="addToCart('${p.id}')">Add to Cart</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load catalog:", err);
  }
}

async function executeSearch() {
  const query = document.getElementById("searchInput").value.trim();
  if (!query) {
    loadCatalog();
    return;
  }

  try {
    const res = await fetch("/api/v1/search/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query })
    });
    const json = await res.json();
    const grid = document.getElementById("productGrid");

    if (!json.data || json.data.length === 0) {
      grid.innerHTML = `<p style="color: var(--text-muted);">No search results matching "${escapeHtml(query)}".</p>`;
      return;
    }

    grid.innerHTML = json.data.map(p => `
      <div class="card">
        <div>
          <span class="badge badge-success">Relevance Score: ${p.relevance_score}</span>
          <h3 class="card-title" style="margin-top: 0.5rem;">${escapeHtml(p.title)}</h3>
          <div class="card-price">$${p.price.toFixed(2)}</div>
        </div>
        <button class="btn btn-primary" onclick="addToCart('${p.product_id}')">Add to Cart</button>
      </div>
    `).join("");
  } catch (err) {
    console.error("Search failed:", err);
  }
}

async function addToCart(productId) {
  if (!state.authToken) {
    alert("Please log in to add items to your cart.");
    return;
  }
  try {
    const res = await fetch("/api/v1/cart/items", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({ product_id: productId, quantity: 1 })
    });
    const json = await res.json();
    if (json.success) {
      alert("Product added to cart!");
      loadCartSummary();
    } else {
      alert(json.message || "Failed to add to cart.");
    }
  } catch (err) {
    console.error("Add to cart failed:", err);
  }
}

async function loadCartSummary() {
  if (!state.authToken) return;
  try {
    const res = await fetch("/api/v1/cart", {
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    if (json.success) {
      state.cart = json.data;
      document.getElementById("cartCount").textContent = json.data.items.length;
    }
  } catch (err) {
    console.error("Cart loading failed:", err);
  }
}

async function loadSellerAnalytics() {
  if (!state.authToken) return;
  try {
    const res = await fetch("/api/v1/analytics/seller", {
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    if (json.success) {
      const d = json.data;
      document.getElementById("sellerRevenue").textContent = `$${d.total_revenue_earned.toFixed(2)}`;
      document.getElementById("sellerOrders").textContent = d.total_orders_fulfilled;
      document.getElementById("sellerProducts").textContent = d.total_products_listed;
    }
  } catch (err) {
    console.error("Seller analytics error:", err);
  }
}

async function loadAdminAnalytics() {
  if (!state.authToken) return;
  try {
    const res = await fetch("/api/v1/analytics/admin", {
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    if (json.success) {
      const d = json.data;
      document.getElementById("adminGrossRev").textContent = `$${d.total_gross_revenue.toFixed(2)}`;
      document.getElementById("adminTotalOrders").textContent = d.total_orders;
      document.getElementById("adminUsers").textContent = d.total_users;
      document.getElementById("adminFraudFlags").textContent = d.flagged_fraud_events;

      const logList = document.getElementById("auditLogList");
      logList.innerHTML = d.recent_audit_logs.map(l => `
        <div>[${l.timestamp.substring(11, 19)}] ${l.action} -> ${l.entity} (ID: ${l.id.substring(0,8)})</div>
      `).join("");
    }
  } catch (err) {
    console.error("Admin analytics error:", err);
  }
}

function updateAuthUI() {
  const btn = document.getElementById("authBtn");
  if (state.currentUser) {
    btn.textContent = `Logged in: ${state.currentUser.email.split('@')[0]}`;
  } else {
    btn.textContent = "Login / Register";
  }
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
