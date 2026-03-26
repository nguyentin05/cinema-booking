const genreSelectBox = document.getElementById('genreSelect');

if (genreSelectBox) {
    genreSelectBox.addEventListener('change', function() {
        const selectedValue = this.value

        if (selectedValue) {
            window.location.href = '/?genre_id=' + selectedValue
        } else {
            window.location.href = '/'
        }
    })
}