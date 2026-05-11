function switchArtwork(thumb) {
    var container = thumb.closest('.cardContainer');
    var mainImg = container.querySelector('#img_card_main, .img-card-main');
    if (mainImg) mainImg.src = thumb.dataset.fullImage;
    thumb.parentElement.querySelectorAll('.galleryThumb').forEach(function(t) {
        t.classList.remove('galleryThumb--active');
    });
    thumb.classList.add('galleryThumb--active');
}
