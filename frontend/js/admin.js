/**
 * admin.js — Admin dashboard logic
 *
 * This page is protected — only logged-in admins can see it.
 * On load, requireAuth() checks the stored JWT token.
 * If it's invalid or missing, the user is sent to login.html.
 *
 * Features:
 *   - Live stats (total listings, total value, enquiry count)
 *   - Listings table with Edit and Delete buttons
 *   - Add/Edit modal form (same form, different behaviour)
 *   - Enquiries table
 */

async function init() {
  // Check auth before showing anything — redirects to login if not logged in
  const user = await requireAuth();
  if (!user) return;

  // Show the admin's username in the dashboard
  document.getElementById('admin-username').textContent = `Logged in as: ${user.username}`;

  // Load data for both tables in parallel (faster than one after the other)
  await Promise.all([loadListings(), loadEnquiries()]);
}

// ─────────────────────────────────────────────
// LISTINGS TABLE
// ─────────────────────────────────────────────

async function loadListings() {
  const tbody = document.getElementById('listings-tbody');

  try {
    const listings = await api.get('/listings/');

    // Update the stats cards
    const totalValue = listings.reduce((sum, l) => sum + l.price, 0);
    document.getElementById('stat-total').textContent = listings.length;
    document.getElementById('stat-live').textContent  = listings.length;
    document.getElementById('stat-value').textContent = '$' + (totalValue / 1000000).toFixed(2) + 'M';

    if (!listings.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);">No listings yet. Add one!</td></tr>';
      return;
    }

    tbody.innerHTML = listings.map(l => {
      const facs = parseFacilities(l.facilities);
      return `
        <tr>
          <td class="td-title">${l.emoji || '🏠'} ${l.title}</td>
          <td style="color:var(--muted);">${l.location}</td>
          <td class="td-price">${fmt(l.price)}</td>
          <td>${facs.slice(0, 3).map(f => `<span class="fac">${f}</span>`).join(' ')}</td>
          <td><span class="status-pill">Live</span></td>
          <td>
            <button class="btn-edit" onclick="openEditModal(${l.id})">Edit</button>
            <button class="btn-del"  onclick="deleteListing(${l.id}, '${l.title.replace(/'/g, "\\'")}')">Delete</button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:#E24B4A;text-align:center;">Failed to load listings: ${err.message}</td></tr>`;
  }
}

// ─────────────────────────────────────────────
// ENQUIRIES TABLE
// ─────────────────────────────────────────────

async function loadEnquiries() {
  const tbody = document.getElementById('enquiries-tbody');

  try {
    const enquiries = await api.get('/enquiries/');

    // Update the enquiries stat card
    document.getElementById('stat-enquiries').textContent = enquiries.length;

    if (!enquiries.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--muted);">No enquiries yet.</td></tr>';
      return;
    }

    tbody.innerHTML = enquiries.map(e => {
      const date = new Date(e.created_at).toLocaleDateString();
      return `
        <tr>
          <td class="td-title">${e.name}</td>
          <td>${e.email}</td>
          <td>${e.phone || '—'}</td>
          <td>#${e.listing_id}</td>
          <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${e.message || '—'}</td>
          <td style="color:var(--muted);">${date}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:#E24B4A;text-align:center;">Failed to load enquiries.</td></tr>`;
  }
}

// ─────────────────────────────────────────────
// ADD / EDIT MODAL
// ─────────────────────────────────────────────

/** Open the modal in "Add" mode (empty form) */
function openModal() {
  document.getElementById('modal-title').textContent = 'Add New Listing';
  document.getElementById('listing-form').reset();
  document.getElementById('edit-id').value = '';
  document.getElementById('modal-error').style.display = 'none';
  document.getElementById('save-btn').textContent = 'Save Listing';
  document.getElementById('overlay').classList.add('open');
}

/** Open the modal in "Edit" mode (pre-filled with existing data) */
async function openEditModal(id) {
  try {
    const l = await api.get(`/listings/${id}`);

    document.getElementById('modal-title').textContent  = 'Edit Listing';
    document.getElementById('edit-id').value            = l.id;
    document.getElementById('f-title').value            = l.title;
    document.getElementById('f-price').value            = l.price;
    document.getElementById('f-location').value         = l.location;
    document.getElementById('f-beds').value             = l.beds;
    document.getElementById('f-baths').value            = l.baths;
    document.getElementById('f-sqm').value              = l.sqm;
    document.getElementById('f-emoji').value            = l.emoji || '';
    document.getElementById('f-desc').value             = l.description || '';
    document.getElementById('f-facilities').value       = l.facilities || '';
    document.getElementById('modal-error').style.display = 'none';
    document.getElementById('save-btn').textContent     = 'Update Listing';

    document.getElementById('overlay').classList.add('open');
  } catch (err) {
    alert('Failed to load listing: ' + err.message);
  }
}

function closeModal() {
  document.getElementById('overlay').classList.remove('open');
}

/** Handle the modal form submit — creates or updates a listing */
async function saveListing(event) {
  event.preventDefault();

  const saveBtn  = document.getElementById('save-btn');
  const errorDiv = document.getElementById('modal-error');
  const editId   = document.getElementById('edit-id').value;

  saveBtn.textContent = 'Saving...';
  saveBtn.disabled    = true;
  errorDiv.style.display = 'none';

  // Collect all form values
  const data = {
    title:       document.getElementById('f-title').value,
    price:       parseFloat(document.getElementById('f-price').value),
    location:    document.getElementById('f-location').value,
    beds:        parseInt(document.getElementById('f-beds').value),
    baths:       parseInt(document.getElementById('f-baths').value),
    sqm:         parseInt(document.getElementById('f-sqm').value),
    emoji:       document.getElementById('f-emoji').value || '🏠',
    description: document.getElementById('f-desc').value,
    facilities:  document.getElementById('f-facilities').value,
  };

  try {
    if (editId) {
      // Edit mode: PUT /listings/{id}
      await api.put(`/listings/${editId}`, data);
    } else {
      // Add mode: POST /listings/
      await api.post('/listings/', data);
    }

    closeModal();
    loadListings(); // Refresh the table

  } catch (err) {
    errorDiv.textContent   = err.message;
    errorDiv.style.display = 'block';
    saveBtn.textContent    = editId ? 'Update Listing' : 'Save Listing';
    saveBtn.disabled       = false;
  }
}

/** Delete a listing after confirmation */
async function deleteListing(id, title) {
  // Ask the user to confirm before deleting — this is irreversible
  const confirmed = confirm(`Delete "${title}"?\n\nThis cannot be undone.`);
  if (!confirmed) return;

  try {
    await api.delete(`/listings/${id}`);
    loadListings(); // Refresh the table
  } catch (err) {
    alert('Failed to delete: ' + err.message);
  }
}

// Close modal when clicking the dark overlay background
document.getElementById('overlay').addEventListener('click', (e) => {
  if (e.target === document.getElementById('overlay')) closeModal();
});

init();
