/**
 * detail.js — Property detail page logic
 *
 * How it works:
 *   1. Read the listing ID from the URL: detail.html?id=3
 *   2. Fetch that listing from GET /listings/3
 *   3. Render the full detail view
 *   4. Handle the enquiry form submission (POST /enquiries)
 */

async function init() {
  // Read ?id= from the URL
  const params = new URLSearchParams(window.location.search);
  const id     = params.get('id');

  if (!id) {
    // No ID in the URL — redirect home
    window.location.href = 'index.html';
    return;
  }

  try {
    // Fetch this one listing from the API
    const listing = await api.get(`/listings/${id}`);
    renderDetail(listing);
    document.title = `${listing.title} — agendCS`;
  } catch (err) {
    document.getElementById('detail-wrap').innerHTML =
      '<div class="loading">Property not found. <a href="index.html">← Back to listings</a></div>';
  }
}

/** Render the full detail view for a listing */
function renderDetail(l) {
  const facs = parseFacilities(l.facilities);
  const bg   = l.image_url
    ? `background-image: url('${l.image_url}'); background-size: cover; background-position: center;`
    : `background: linear-gradient(135deg, #9FE1CB, #1D9E75);`;

  document.getElementById('detail-wrap').innerHTML = `
    <a class="back-btn" href="index.html">← Back to listings</a>

    <!-- GALLERY -->
    <div class="detail-gallery">
      <div class="gal-main" style="${bg}">
        ${!l.image_url ? `<span style="font-size:80px;">${l.emoji || '🏠'}</span>` : ''}
      </div>
      <div class="gal-sub">
        <div class="gal-sm">🌿</div>
        <div class="gal-sm">🛁</div>
      </div>
    </div>

    <!-- DETAIL GRID: info on left, enquiry card on right -->
    <div class="detail-grid">

      <!-- LEFT: property info -->
      <div class="detail-info">
        <div class="detail-price-row">
          <div class="detail-price">${fmt(l.price)}${l.listing_type === 'rent' ? '<span style="font-size:16px;font-weight:400;"> /mo</span>' : ''}</div>
          <span class="card-tag">${l.listing_type === 'rent' ? 'For Rent' : 'For Sale'}</span>
        </div>
        <h1>${l.title}</h1>
        <div class="detail-loc">📍 ${l.location}</div>

        <div class="detail-meta">
          <span class="detail-meta-item">🛏 ${l.beds} Bedrooms</span>
          <span class="detail-meta-item">🚿 ${l.baths} Bathrooms</span>
          <span class="detail-meta-item">📐 ${l.sqm} m²</span>
        </div>

        <div class="section-title">About this property</div>
        <p class="detail-desc">${l.description || 'No description available.'}</p>

        <div class="section-title">Facilities & Amenities</div>
        <div class="fac-grid">
          ${facs.map(f => `
            <div class="fac-item">
              <div class="fac-icon">${FAC_ICONS[f] || '✓'}</div>
              <div class="fac-name">${f}</div>
            </div>
          `).join('')}
        </div>
      </div>

      <!-- RIGHT: enquiry form -->
      <div>
        <div class="enquiry-card">
          <h3>Enquire Now</h3>
          <form id="enq-form" onsubmit="submitEnquiry(event, ${l.id})">
            <input class="enq-input" name="name"    type="text"  placeholder="Your full name"   required/>
            <input class="enq-input" name="phone"   type="tel"   placeholder="Phone number"/>
            <input class="enq-input" name="email"   type="email" placeholder="Email address"    required/>
            <textarea class="enq-input" name="message" rows="3"  placeholder="I'm interested in this property..." style="resize:none;"></textarea>
            <button class="enq-submit" type="submit">Send Enquiry</button>
          </form>
          <div class="enq-success" id="enq-success">
            ✓ Enquiry sent! We'll be in touch shortly.
          </div>
          <div class="agent-info">
            <div class="agent-avatar">SR</div>
            <div>
              <div class="agent-name">Sophea Ros</div>
              <div class="agent-role">Senior Property Consultant</div>
            </div>
          </div>
        </div>
      </div>

    </div>
  `;
}

/** Handle the enquiry form submission */
async function submitEnquiry(event, listingId) {
  event.preventDefault(); // Don't reload the page

  const form    = document.getElementById('enq-form');
  const success = document.getElementById('enq-success');
  const btn     = form.querySelector('.enq-submit');

  btn.textContent = 'Sending...';
  btn.disabled    = true;

  try {
    // Collect form field values
    const data = {
      listing_id: listingId,
      name:       form.name.value,
      phone:      form.phone.value,
      email:      form.email.value,
      message:    form.message.value,
    };

    // POST to /enquiries
    await api.post('/enquiries/', data);

    // Show success message, hide the form
    form.style.display    = 'none';
    success.style.display = 'block';

  } catch (err) {
    btn.textContent = 'Send Enquiry';
    btn.disabled    = false;
    alert('Failed to send enquiry: ' + err.message);
  }
}

init();
