/**
 * listings.js — Home page logic
 *
 * Responsibilities:
 *   1. On page load, fetch all listings from the API
 *   2. Render them as cards in the grid
 *   3. Handle search/filter (sends query params to the API)
 *   4. Handle sort (client-side, since we already have the data)
 *
 * Key difference from the mockup:
 *   Before: data was a hardcoded JS array at the top of the file
 *   Now: data comes from GET /listings/ on our FastAPI backend
 */

// Keep a copy of all fetched listings so sorting doesn't need another API call
let allListings = [];

/** Called once when the page loads */
async function init() {
  await loadListings();
}

/**
 * Fetch listings from the API and render them.
 * Reads current filter values from the search bar inputs.
 */
async function loadListings() {
  const grid    = document.getElementById('grid');
  const noRes   = document.getElementById('no-results');
  const label   = document.getElementById('result-label');
  const statNum = document.getElementById('stat-total');

  // Show a loading state while we wait for the API
  grid.innerHTML = '<div class="loading">Loading properties...</div>';
  noRes.style.display = 'none';

  try {
    // Build query params from the search bar values
    const params = {
      location:  document.getElementById('s-loc').value,
      max_price: document.getElementById('s-price').value,
    };

    // Fetch from GET /listings/?location=...&max_price=...
    const listings = await api.get('/listings/', params);

    // Apply text search client-side (fast, no extra API call needed)
    const query = document.getElementById('s-text').value.toLowerCase();
    allListings = listings.filter(l =>
      !query ||
      l.title.toLowerCase().includes(query) ||
      l.location.toLowerCase().includes(query)
    );

    // Update the stat counter and result label
    statNum.textContent = allListings.length + '+';
    label.textContent = `Showing ${allListings.length} propert${allListings.length === 1 ? 'y' : 'ies'}`;

    renderGrid(allListings);

  } catch (err) {
    grid.innerHTML = `<div class="loading">Failed to load listings. Is the backend running?</div>`;
    console.error(err);
  }
}

/**
 * Render an array of listing objects as cards in the grid.
 * Each card links to detail.html?id=X so clicking opens the detail page.
 */
function renderGrid(listings) {
  const grid  = document.getElementById('grid');
  const noRes = document.getElementById('no-results');

  if (!listings.length) {
    grid.innerHTML = '';
    noRes.style.display = 'block';
    return;
  }

  noRes.style.display = 'none';

  // Build the background style — use image_url if available, otherwise the gradient
  grid.innerHTML = listings.map(l => {
    const facs = parseFacilities(l.facilities);
    const bg   = l.image_url
      ? `background-image: url('${l.image_url}'); background-size: cover; background-position: center;`
      : `background: linear-gradient(135deg, #9FE1CB, #1D9E75);`;

    return `
      <a class="card" href="detail.html?id=${l.id}">
        <div class="card-img" style="${bg}">
          ${!l.image_url ? `<div style="font-size:72px;position:relative;z-index:1;">${l.emoji || '🏠'}</div>` : ''}
          <div class="img-overlay"></div>
          <div class="card-badge">For Sale</div>
          <div class="card-fav">🤍</div>
        </div>
        <div class="card-body">
          <div class="card-top">
            <div class="card-price">${fmt(l.price)}</div>
            <span class="card-tag">${l.location}</span>
          </div>
          <div class="card-title">${l.title}</div>
          <div class="card-loc">📍 ${l.location}</div>
          <div class="divider"></div>
          <div class="card-meta">
            <span class="meta-item">🛏 ${l.beds} beds</span>
            <span class="meta-item">🚿 ${l.baths} baths</span>
            <span class="meta-item">📐 ${l.sqm}m²</span>
          </div>
          <div class="card-facilities">
            ${facs.slice(0, 4).map(f => `<span class="fac">${f}</span>`).join('')}
            ${facs.length > 4 ? `<span class="fac">+${facs.length - 4}</span>` : ''}
          </div>
        </div>
      </a>
    `;
  }).join('');
}

/** Called when any filter input changes — re-fetches from the API */
function handleSearch() {
  loadListings();
}

/** Sort the already-loaded listings without another API call */
function handleSort(dir) {
  if (!dir) {
    renderGrid(allListings);
    return;
  }
  const sorted = [...allListings].sort((a, b) =>
    dir === 'asc' ? a.price - b.price : b.price - a.price
  );
  renderGrid(sorted);
}

// Start when the page loads
init();
