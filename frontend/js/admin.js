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
  document.getElementById('modal-title').textContent  = 'Add New Listing';
  document.getElementById('listing-form').reset();
  document.getElementById('edit-id').value            = '';
  document.getElementById('modal-error').style.display = 'none';
  document.getElementById('save-btn').textContent     = 'Save Listing';
  document.getElementById('upload-section').style.display = 'none'; // Hidden until listing is saved
  resetImagePreview();
  document.getElementById('overlay').classList.add('open');
}

/** Open the modal in "Edit" mode (pre-filled with existing data) */
async function openEditModal(id) {
  try {
    const l = await api.get(`/listings/${id}`);

    document.getElementById('modal-title').textContent   = 'Edit Listing';
    document.getElementById('edit-id').value             = l.id;
    document.getElementById('f-title').value             = l.title;
    document.getElementById('f-price').value             = l.price;
    document.getElementById('f-location').value          = l.location;
    document.getElementById('f-beds').value              = l.beds;
    document.getElementById('f-baths').value             = l.baths;
    document.getElementById('f-sqm').value               = l.sqm;
    document.getElementById('f-emoji').value             = l.emoji || '';
    document.getElementById('f-desc').value              = l.description || '';
    document.getElementById('f-facilities').value        = l.facilities || '';
    document.getElementById('modal-error').style.display = 'none';
    document.getElementById('save-btn').textContent      = 'Update Listing';

    // Show the upload section for existing listings (we already have an ID)
    document.getElementById('upload-section').style.display = 'block';

    // If the listing already has an image, show a preview of it
    if (l.image_url) {
      document.getElementById('upload-preview').innerHTML = `<img src="${l.image_url}" style="max-height:120px;border-radius:8px;object-fit:cover;"/>`;
      document.getElementById('upload-label').textContent = 'Click to change photo';
    } else {
      resetImagePreview();
    }

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
    let listing;
    if (editId) {
      // Edit mode: PUT /listings/{id}
      listing = await api.put(`/listings/${editId}`, data);
    } else {
      // Add mode: POST /listings/ — we get back the new listing with its ID
      listing = await api.post('/listings/', data);
      // Show the upload section now that we have an ID to attach the image to
      document.getElementById('edit-id').value = listing.id;
      document.getElementById('upload-section').style.display = 'block';
    }

    // If a new image file was selected, upload it now that we have the listing ID
    const imageFile = document.getElementById('f-image').files[0];
    if (imageFile) {
      await uploadImage(listing.id, imageFile);
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

/**
 * Upload an image file for a listing.
 * Uses FormData (multipart/form-data) — the standard way to send files over HTTP.
 * Note: we bypass api.js here because file uploads need special handling.
 */
async function uploadImage(listingId, file) {
  const formData = new FormData();
  formData.append('file', file); // 'file' must match the parameter name in the backend

  const token = localStorage.getItem('nestkh_token');
  const res   = await fetch(`http://localhost:8000/listings/${listingId}/upload-image`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
    // Note: do NOT set Content-Type here — the browser sets it automatically
    //       including the required "boundary" string for multipart data
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Image upload failed');
  }
}

/** Show a preview of the selected image before uploading */
function previewImage(input) {
  const file = input.files[0];
  if (!file) return;

  const reader = new FileReader(); // FileReader reads local files in the browser
  reader.onload = (e) => {
    document.getElementById('upload-preview').innerHTML =
      `<img src="${e.target.result}" style="max-height:120px;border-radius:8px;object-fit:cover;"/>`;
    document.getElementById('upload-label').textContent = file.name;
  };
  reader.readAsDataURL(file); // Converts the file to a base64 data URL for preview
}

/** Reset the image upload zone back to its default state */
function resetImagePreview() {
  document.getElementById('upload-preview').innerHTML = '<div style="font-size:28px;">📁</div>';
  document.getElementById('upload-label').textContent = 'Click to upload a photo (JPG, PNG — max 5MB)';
  document.getElementById('f-image').value = '';
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
