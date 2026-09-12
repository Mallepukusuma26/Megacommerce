/**
 * MegaCommerce Master SPA Frontend Controller
 * Zero External API Key Architecture
 */

let state = {
  authToken: localStorage.getItem("megacommerce_token") || null,
  currentUser: JSON.parse(localStorage.getItem("megacommerce_user") || "null"),
  cart: { items: [], grand_total: 0.0 },
  wishlist: []
};

// Initialize Application on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  loadCategories();
  loadCatalog();
  updateAuthUI();
  handleInitialHash();

  if (state.authToken) {
    loadCartSummary();
    loadWishlist();
  }
});

// Routing & Portal Switching
function switchPortal(portalName) {
  document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".portal-view").forEach(el => el.classList.remove("active"));

  if (portalName === "customer") {
    document.getElementById("navCustomer")?.classList.add("active");
    document.getElementById("customerPortal").classList.add("active");
    window.location.hash = "#customer";
    loadCatalog();
  } else if (portalName === "seller") {
    document.getElementById("navSeller")?.classList.add("active");
    document.getElementById("sellerPortal").classList.add("active");
    window.location.hash = "#seller";
    loadSellerAnalytics();
  } else if (portalName === "admin") {
    document.getElementById("navAdmin")?.classList.add("active");
    document.getElementById("adminPortal").classList.add("active");
    window.location.hash = "#admin";
    loadAdminAnalytics();
  }
}

function showCustomerSubTab(tabName) {
  document.getElementById("subTabCatalog").style.display = tabName === "catalog" ? "block" : "none";
  document.getElementById("subTabOrders").style.display = tabName === "orders" ? "block" : "none";
  document.getElementById("subTabReturns").style.display = tabName === "returns" ? "block" : "none";

  if (tabName === "orders") loadCustomerOrders();
}

function handleInitialHash() {
  const hash = window.location.hash.replace("#", "");
  if (hash === "seller") switchPortal("seller");
  else if (hash === "admin") switchPortal("admin");
  else if (hash === "register" || hash === "login") openAuthModal(hash);
  else switchPortal("customer");
}

// -------------------------------------------------------------------
// AUTHENTICATION MODAL & PERSISTENCE (REGISTER & LOGIN)
// -------------------------------------------------------------------

function openAuthModal(defaultTab = "login") {
  document.getElementById("authModal").style.display = "flex";
  switchAuthTab(defaultTab);
}

function closeAuthModal() {
  document.getElementById("authModal").style.display = "none";
}

function switchAuthTab(tab) {
  const loginForm = document.getElementById("loginForm");
  const regForm = document.getElementById("registerForm");
  const tabLoginBtn = document.getElementById("tabLoginBtn");
  const tabRegBtn = document.getElementById("tabRegisterBtn");

  if (tab === "login") {
    loginForm.style.display = "block";
    regForm.style.display = "none";
    tabLoginBtn.classList.add("active");
    tabRegBtn.classList.remove("active");
    document.getElementById("authModalTitle").textContent = "User Login";
  } else {
    loginForm.style.display = "none";
    regForm.style.display = "block";
    tabRegBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    document.getElementById("authModalTitle").textContent = "Create Account";
  }
}

async function handleLoginSubmit(event) {
  event.preventDefault();
  const email = document.getElementById("loginEmail").value.trim();
  const password = document.getElementById("loginPassword").value;

  try {
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    const json = await res.json();

    if (json.access_token) {
      state.authToken = json.access_token;
      state.currentUser = json.user;
      localStorage.setItem("megacommerce_token", json.access_token);
      localStorage.setItem("megacommerce_user", JSON.stringify(json.user));

      showToast(`Welcome back, ${json.user.full_name}!`, "success");
      closeAuthModal();
      updateAuthUI();
      loadCartSummary();

      if (json.user.role === "SELLER") switchPortal("seller");
      else if (json.user.role === "ADMIN") switchPortal("admin");
      else switchPortal("customer");
    } else {
      showToast(json.message || "Invalid credentials provided.", "error");
    }
  } catch (err) {
    showToast("Login failed. Please check network connection.", "error");
    console.error("Login error:", err);
  }
}

async function handleRegisterSubmit(event) {
  event.preventDefault();
  const full_name = document.getElementById("regName").value.trim();
  const email = document.getElementById("regEmail").value.trim();
  const phone = document.getElementById("regPhone").value.trim();
  const password = document.getElementById("regPassword").value;
  const role = document.getElementById("regRole").value;

  try {
    const res = await fetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name, email, phone, password, role })
    });
    const json = await res.json();

    if (json.id || json.success) {
      showToast("Account created successfully! Please log in now.", "success");
      switchAuthTab("login");
      document.getElementById("loginEmail").value = email;
    } else {
      showToast(json.message || "Registration failed.", "error");
    }
  } catch (err) {
    showToast("Registration error. Email may already be in use.", "error");
    console.error("Registration error:", err);
  }
}

function logout() {
  state.authToken = null;
  state.currentUser = null;
  state.cart = { items: [], grand_total: 0.0 };
  localStorage.removeItem("megacommerce_token");
  localStorage.removeItem("megacommerce_user");

  updateAuthUI();
  showToast("You have logged out.", "info");
  switchPortal("customer");
}

function updateAuthUI() {
  const container = document.getElementById("authNavContainer");
  if (state.currentUser) {
    container.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <span style="font-size: 0.9rem; color: var(--text-color);">Hi, <strong>${escapeHtml(state.currentUser.full_name.split(' ')[0])}</strong> (${state.currentUser.role})</span>
        <button class="btn btn-secondary" onclick="logout()">Logout</button>
      </div>
    `;
  } else {
    container.innerHTML = `<button class="btn btn-secondary" id="authBtn" onclick="openAuthModal('login')">Login / Register</button>`;
  }
}

// -------------------------------------------------------------------
// CATALOG & SEARCH
// -------------------------------------------------------------------

async function loadCategories() {
  try {
    const res = await fetch("/api/v1/catalog/categories");
    const json = await res.json();
    if (json.success) {
      const select = document.getElementById("categorySelect");
      const pCatSelect = document.getElementById("pCategory");
      
      select.innerHTML = '<option value="">All Categories</option>';
      if (pCatSelect) pCatSelect.innerHTML = '';

      json.data.forEach(cat => {
        const opt = document.createElement("option");
        opt.value = cat.id;
        opt.textContent = cat.name;
        select.appendChild(opt);

        if (pCatSelect) {
          const opt2 = document.createElement("option");
          opt2.value = cat.id;
          opt2.textContent = cat.name;
          pCatSelect.appendChild(opt2);
        }
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
          <button class="btn btn-secondary" onclick="addToWishlist('${p.id}')">❤️</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Failed to load catalog:", err);
  }
}

function handleSearchInput(event) {
  if (event.key === "Enter") {
    executeSearch();
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
          <div class="card-price" style="font-weight: 700; margin-bottom: 0.5rem;">$${p.price.toFixed(2)}</div>
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <button class="btn btn-primary" style="flex: 1;" onclick="addToCart('${p.product_id}')">Add to Cart</button>
          <button class="btn btn-secondary" onclick="addToWishlist('${p.product_id}')">❤️</button>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Search failed:", err);
  }
}

// -------------------------------------------------------------------
// CART & CHECKOUT DRAWER
// -------------------------------------------------------------------

function openCartDrawer() {
  if (!state.authToken) {
    showToast("Please log in to view your cart.", "info");
    openAuthModal("login");
    return;
  }
  document.getElementById("cartModal").style.display = "flex";
  loadCartSummary();
}

function closeCartDrawer() {
  document.getElementById("cartModal").style.display = "none";
}

async function addToCart(productId) {
  if (!state.authToken) {
    showToast("Please log in to add items to your cart.", "info");
    openAuthModal("login");
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
      showToast("Item added to cart!", "success");
      loadCartSummary();
    } else {
      showToast(json.message || "Failed to add to cart.", "error");
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
      document.getElementById("cartGrandTotal").textContent = `$${json.data.grand_total.toFixed(2)}`;

      const listContainer = document.getElementById("cartItemsList");
      if (json.data.items.length === 0) {
        listContainer.innerHTML = '<p style="color: var(--text-muted);">Your cart is currently empty.</p>';
      } else {
        listContainer.innerHTML = json.data.items.map(item => `
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding: 0.5rem 0;">
            <div>
              <div style="font-weight: 600;">${escapeHtml(item.product_title || 'Product')}</div>
              <div style="font-size: 0.85rem; color: var(--text-muted);">Qty: ${item.quantity} × $${item.unit_price.toFixed(2)}</div>
            </div>
            <div style="display: flex; align-items: center; gap: 0.5rem;">
              <span style="font-weight: 700;">$${item.total_price.toFixed(2)}</span>
              <button class="btn btn-secondary" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;" onclick="removeFromCart('${item.id}')">✕</button>
            </div>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Cart loading failed:", err);
  }
}

async function removeFromCart(itemId) {
  try {
    const res = await fetch(`/api/v1/cart/items/${itemId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    if (json.success) {
      showToast("Item removed from cart.", "info");
      loadCartSummary();
    }
  } catch (err) {
    console.error("Remove cart item failed:", err);
  }
}

function openCheckoutModal() {
  if (state.cart.items.length === 0) {
    showToast("Your cart is empty. Add products before checking out.", "info");
    return;
  }
  closeCartDrawer();
  document.getElementById("checkoutModal").style.display = "flex";
}

function closeCheckoutModal() {
  document.getElementById("checkoutModal").style.display = "none";
}

async function handleCheckoutSubmit(event) {
  event.preventDefault();
  const shipping_address = document.getElementById("chkAddress").value.trim();
  const coupon_code = document.getElementById("chkCoupon").value.trim();
  const payment_method = document.getElementById("chkPaymentMethod").value;

  try {
    const res = await fetch("/api/v1/orders/checkout", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({ shipping_address, coupon_code, payment_method })
    });
    const json = await res.json();

    if (json.success) {
      showToast("Order placed successfully! Downloading PDF Invoice...", "success");
      closeCheckoutModal();
      loadCartSummary();

      // Trigger automatic PDF invoice download
      if (json.data.order_id) {
        window.open(`/api/v1/orders/${json.data.order_id}/invoice`, "_blank");
      }
      showCustomerSubTab("orders");
    } else {
      showToast(json.message || "Checkout failed.", "error");
    }
  } catch (err) {
    console.error("Checkout submit failed:", err);
    showToast("Checkout failed. Check payment gateway simulator.", "error");
  }
}

// -------------------------------------------------------------------
// WISHLIST & ORDERS
// -------------------------------------------------------------------

async function addToWishlist(productId) {
  if (!state.authToken) {
    showToast("Please log in to manage your wishlist.", "info");
    openAuthModal("login");
    return;
  }
  try {
    const res = await fetch("/api/v1/cart/wishlist", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({ product_id: productId })
    });
    const json = await res.json();
    if (json.success) {
      showToast("Item added to wishlist! ❤️", "success");
      loadWishlist();
    }
  } catch (err) {
    console.error("Wishlist add failed:", err);
  }
}

async function loadWishlist() {
  if (!state.authToken) return;
  try {
    const res = await fetch("/api/v1/cart/wishlist", {
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    if (json.success) {
      state.wishlist = json.data;
      document.getElementById("wishlistCount").textContent = json.data.length;
      
      const listContainer = document.getElementById("wishlistItemsList");
      if (json.data.length === 0) {
        listContainer.innerHTML = '<p style="color: var(--text-muted);">No items in wishlist.</p>';
      } else {
        listContainer.innerHTML = json.data.map(item => `
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding: 0.5rem 0;">
            <div>
              <div style="font-weight: 600;">${escapeHtml(item.product_title || 'Product')}</div>
              <div style="font-size: 0.85rem; color: var(--text-muted);">$${item.unit_price ? item.unit_price.toFixed(2) : '0.00'}</div>
            </div>
            <button class="btn btn-primary" style="padding: 0.3rem 0.6rem; font-size: 0.85rem;" onclick="addToCart('${item.product_id}')">Move to Cart</button>
          </div>
        `).join("");
      }
    }
  } catch (err) {
    console.error("Wishlist load failed:", err);
  }
}

function openWishlistModal() {
  if (!state.authToken) {
    openAuthModal("login");
    return;
  }
  document.getElementById("wishlistModal").style.display = "flex";
  loadWishlist();
}

function closeWishlistModal() {
  document.getElementById("wishlistModal").style.display = "none";
}

async function loadCustomerOrders() {
  if (!state.authToken) return;
  try {
    const res = await fetch("/api/v1/orders/history", {
      headers: { "Authorization": `Bearer ${state.authToken}` }
    });
    const json = await res.json();
    const container = document.getElementById("customerOrdersList");

    if (!json.data || json.data.length === 0) {
      container.innerHTML = '<p style="color: var(--text-muted);">You have no previous orders.</p>';
      return;
    }

    container.innerHTML = json.data.map(ord => `
      <div style="background: var(--surface-dark); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700;">Order #${ord.order_number}</span>
          <span class="badge badge-success">${ord.status}</span>
        </div>
        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-muted);">
          Total Amount: <strong>$${ord.total_amount.toFixed(2)}</strong> | Payment: ${ord.payment_method}
        </div>
        <div style="margin-top: 0.75rem; display: flex; gap: 0.5rem;">
          <a class="btn btn-secondary" style="font-size: 0.85rem;" href="/api/v1/orders/${ord.id}/invoice" target="_blank">📄 Download Invoice PDF</a>
        </div>
      </div>
    `).join("");
  } catch (err) {
    console.error("Customer orders load failed:", err);
  }
}

// -------------------------------------------------------------------
// SELLER PORTAL HANDLERS
// -------------------------------------------------------------------

function openAddProductModal() {
  if (!state.authToken || (state.currentUser && state.currentUser.role !== "SELLER" && state.currentUser.role !== "ADMIN")) {
    showToast("Please log in with a SELLER account to create products.", "error");
    openAuthModal("login");
    return;
  }
  document.getElementById("newProductModal").style.display = "flex";
}

function closeAddProductModal() {
  document.getElementById("newProductModal").style.display = "none";
}

async function handleCreateProductSubmit(event) {
  event.preventDefault();
  const title = document.getElementById("pTitle").value.trim();
  const category_id = document.getElementById("pCategory").value;
  const price = parseFloat(document.getElementById("pPrice").value);
  const stock_quantity = parseInt(document.getElementById("pStock").value);
  const description = document.getElementById("pDesc").value.trim();

  try {
    const res = await fetch("/api/v1/catalog/products", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${state.authToken}`
      },
      body: JSON.stringify({ title, category_id, price, stock_quantity, description })
    });
    const json = await res.json();

    if (json.id || json.success) {
      showToast("Product listing created successfully!", "success");
      closeAddProductModal();
      loadSellerAnalytics();
    } else {
      showToast(json.message || "Failed to create product.", "error");
    }
  } catch (err) {
    console.error("Create product failed:", err);
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

// -------------------------------------------------------------------
// ADMIN PORTAL HANDLERS
// -------------------------------------------------------------------

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

// -------------------------------------------------------------------
// UTILITY HELPERS
// -------------------------------------------------------------------

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const toast = document.createElement("div");
  const bgColor = type === "success" ? "#10b981" : type === "error" ? "#ef4444" : "#3b82f6";

  toast.style.cssText = `background: ${bgColor}; color: white; padding: 0.75rem 1.25rem; border-radius: 6px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-weight: 500; font-size: 0.9rem; animation: fadeIn 0.2s ease-in-out;`;
  toast.textContent = message;

  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
