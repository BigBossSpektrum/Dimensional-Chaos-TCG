function switchSet(setThumb) {
    var container = setThumb.closest('.cardContainer') || document;

    function updateField(el, text) {
        if (!el) return;
        var icon = el.querySelector('.attr-value .attr-fa-icon, .attr-value .attr-icon');
        el.querySelector('.attr-value').textContent = text;
        if (icon) el.querySelector('.attr-value').prepend(icon);
    }

    updateField(container.querySelector('#info-set-name, .info-set-name'), setThumb.dataset.setName);
    updateField(container.querySelector('#info-set-code, .info-set-code'), setThumb.dataset.setCode);
    updateField(container.querySelector('#info-set-rarity, .info-set-rarity'), setThumb.dataset.setRarity);

    var priceEl = container.querySelector('#info-set-price, .info-set-price');
    if (priceEl) {
        var price = parseFloat(setThumb.dataset.setPrice);
        var displayPrice = (price > 0) ? setThumb.dataset.setPrice : setThumb.dataset.tcgPrice;
        updateField(priceEl, displayPrice + '$');
    }

    setThumb.parentElement.querySelectorAll('.setThumb').forEach(function(s) {
        s.classList.remove('setThumb--active');
    });
    setThumb.classList.add('setThumb--active');
}
