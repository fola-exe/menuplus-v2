/**
 * MenuPlus Invoice Page — JavaScript Controller
 * 
 * INTEGRATION GUIDE:
 * ------------------
 * Replace the `loadInvoiceData()` function with an API call to your backend.
 * The function should return an object matching the `sampleInvoiceData` structure.
 * 
 * Example:
 *   async function loadInvoiceData() {
 *       const invoiceId = getInvoiceIdFromURL();
 *       const res = await fetch(`/api/invoices/${invoiceId}`);
 *       return await res.json();
 *   }
 */

// ============================================
// SAMPLE DATA — Replace with your database call
// ============================================

const sampleInvoiceData = {
    // Company Info
    company: {
        name: "menuplus",
        address: "28 Majaro Street, Onike, Yabba, Lagos. Tel 0802 836 3103",
        contact: "Email: menuplusng@gmail.com   Website: www.menuplusng.com",
        logoUrl: "menuplus_logo.png",
        signatory: {
            name: "Olayinka Adeniyi (Mrs.)",
            title: "Kitchen Manager"
        }
    },

    // Invoice Details
    invoice: {
        number: "OE09012026",
        date: "9TH JANUARY 2026",
        currency: "₦"
    },

    // Client
    client: {
        name: "Oracle Experience",
        location: "Lagos"
    },

    // Event
    event: {
        date: "",       // e.g. "Saturday"
        day: ""         // e.g. "August 30, 2025"
    },

    // Order Items
    items: [
        {
            detail: "Steamed Basmati Rice, Chinese Fried Rice, Singaporean Noodles, Wild Basmati Rice, Fresh Sweet Corn, Buttered/Roasted Potatoes Served with:\n• Shredded beef in black beans and Green Pepper Sauce\n• Chicken in Mixed Vegetable Sauce\n• Fish in sweet and Sour Sauce\n• Prawn in Chilli Sauce\nServe in hot plate",
            quantity: 170,
            unitPrice: 8500
        },
        {
            detail: "Ofada Rice served with ethnic sauce, stewed croaker fish and chicken.",
            quantity: 150,
            unitPrice: 7500
        },
        {
            detail: "Pounded Yam with Efo Egusi/Efo Riro to be served with fish and goat meat",
            quantity: 150,
            unitPrice: 7000
        }
    ],

    // Totals breakdown (after items subtotal)
    charges: [
        { label: "TOTAL", isSubtotal: true },
        { label: "10% service charge", percentage: 10 },
        { label: "Transportation", amount: 50000 }
    ],

    // Deductions (optional)
    deductions: [
        // { label: "Less cow provision", amount: 1000000 }
    ],

    // Amount in words
    amountInWords: "Four Million and Thirty Two Thousand Naira only"
};

// ============================================
// CORE FUNCTIONS
// ============================================

function getInvoiceIdFromURL() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id') || params.get('invoice') || null;
}

/**
 * Load invoice data — REPLACE THIS with your API/database call
 */
async function loadInvoiceData() {
    await new Promise(r => setTimeout(r, 200));
    return sampleInvoiceData;
}

function formatNumber(num) {
    return num.toLocaleString('en-NG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function nl2br(text) {
    return escapeHtml(text).replace(/\n/g, '<br>');
}

// ============================================
// RENDER
// ============================================

function renderInvoice(data) {
    // -- Header --
    if (data.company.logoUrl) {
        document.getElementById('company-logo').src = data.company.logoUrl;
    }
    document.getElementById('company-address-line').textContent = data.company.address;
    document.getElementById('company-contact-line').innerHTML = data.company.contact;

    // -- Client --
    document.getElementById('client-name').textContent = data.client.name;
    document.getElementById('client-location').textContent = data.client.location;

    // -- Invoice Meta --
    document.getElementById('invoice-number').textContent = data.invoice.number;
    document.getElementById('invoice-date').innerHTML = data.invoice.date;

    // -- Items Table --
    renderItems(data);

    // -- Amount in Words --
    document.getElementById('amount-in-words').textContent = data.amountInWords;

    // -- Event --
    const eventDateEl = document.getElementById('event-date');
    const eventDayEl = document.getElementById('event-day');
    if (data.event.date) {
        eventDateEl.textContent = data.event.date;
    }
    if (data.event.day) {
        eventDayEl.textContent = data.event.day;
    }

    // Hide event section if empty
    if (!data.event.date && !data.event.day) {
        document.querySelector('.event-section').style.display = 'none';
    }

    // -- Signature --
    document.getElementById('sig-name').innerHTML = `<em>${escapeHtml(data.company.signatory.name)}</em>`;
    document.getElementById('sig-title').textContent = data.company.signatory.title;

    // -- Page Title --
    document.title = `Invoice ${data.invoice.number} | MenuPlus`;
}

function renderItems(data) {
    const tbody = document.getElementById('items-tbody');
    tbody.innerHTML = '';

    const currency = data.invoice.currency || '₦';
    let subtotal = 0;

    // Render line items
    data.items.forEach((item, idx) => {
        const lineTotal = item.quantity * item.unitPrice;
        subtotal += lineTotal;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${nl2br(item.detail)}</td>
            <td>${item.quantity.toLocaleString()}</td>
            <td>${formatNumber(item.unitPrice)}</td>
            <td>${formatNumber(lineTotal)}</td>
        `;
        tbody.appendChild(tr);
    });

    // Render totals table
    renderTotals(data, subtotal, currency);
}

function renderTotals(data, subtotal, currency) {
    const totalsBody = document.getElementById('totals-tbody');
    totalsBody.innerHTML = '';

    let runningTotal = subtotal;
    const charges = data.charges || [];
    const deductions = data.deductions || [];

    charges.forEach((charge, idx) => {
        const tr = document.createElement('tr');

        if (charge.isSubtotal) {
            // Subtotal row
            tr.innerHTML = `
                <td class="totals-label">${escapeHtml(charge.label)}</td>
                <td class="totals-value">${formatNumber(subtotal)}</td>
            `;
        } else if (charge.percentage) {
            const chargeAmount = subtotal * (charge.percentage / 100);
            runningTotal += chargeAmount;
            tr.innerHTML = `
                <td class="totals-label">${escapeHtml(charge.label)}</td>
                <td class="totals-value">${formatNumber(chargeAmount)}</td>
            `;
        } else if (charge.amount !== undefined) {
            runningTotal += charge.amount;
            tr.innerHTML = `
                <td class="totals-label">${escapeHtml(charge.label)}</td>
                <td class="totals-value">${formatNumber(charge.amount)}</td>
            `;
        }

        totalsBody.appendChild(tr);
    });

    // Grand Total
    const grandTr = document.createElement('tr');
    grandTr.className = 'grand-total-row';
    grandTr.innerHTML = `
        <td class="totals-label">GRAND TOTAL</td>
        <td class="totals-value">${formatNumber(runningTotal)}</td>
    `;
    totalsBody.appendChild(grandTr);

    // Deductions
    deductions.forEach(ded => {
        runningTotal -= ded.amount;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td class="totals-label">${escapeHtml(ded.label)}</td>
            <td class="totals-value">${formatNumber(ded.amount)}</td>
        `;
        totalsBody.appendChild(tr);
    });

    // Final Total (if deductions exist)
    if (deductions.length > 0) {
        const finalTr = document.createElement('tr');
        finalTr.className = 'grand-total-row';
        finalTr.innerHTML = `
            <td class="totals-label">Total</td>
            <td class="totals-value">${formatNumber(runningTotal)}</td>
        `;
        totalsBody.appendChild(finalTr);
    }
}

// ============================================
// PDF GENERATION
// ============================================

async function downloadPDF() {
    const overlay = document.getElementById('loading-overlay');
    overlay.style.display = 'flex';

    try {
        const invoiceEl = document.getElementById('invoice');
        const invoiceNumber = document.getElementById('invoice-number').textContent;

        const opt = {
            margin: [8, 8, 8, 8],
            filename: `MenuPlus_Invoice_${invoiceNumber}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: {
                scale: 2,
                useCORS: true,
                logging: false,
                letterRendering: true
            },
            jsPDF: {
                unit: 'mm',
                format: 'a4',
                orientation: 'portrait'
            },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
        };

        await html2pdf().set(opt).from(invoiceEl).save();
    } catch (err) {
        console.error('PDF generation failed:', err);
        alert('PDF generation failed. Please use the Print button instead.');
    } finally {
        overlay.style.display = 'none';
    }
}

// ============================================
// INIT
// ============================================

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const data = await loadInvoiceData();
        renderInvoice(data);
        document.getElementById('download-pdf-btn').addEventListener('click', downloadPDF);
    } catch (err) {
        console.error('Failed to load invoice:', err);
        document.querySelector('.invoice-page').innerHTML = `
            <div style="text-align:center; padding:80px 24px;">
                <h2 style="color:#E8611A; margin-bottom:8px;">Invoice Not Found</h2>
                <p style="color:#78716C;">The invoice could not be loaded. Please check the link and try again.</p>
            </div>
        `;
    }
});

// ============================================
// PUBLIC API — For integration with your app
// ============================================

window.InvoicePage = {
    load: function(data) { renderInvoice(data); },
    downloadPDF: downloadPDF,
    getInvoiceId: getInvoiceIdFromURL
};
