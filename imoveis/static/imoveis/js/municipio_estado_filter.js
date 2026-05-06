document.addEventListener('DOMContentLoaded', function () {
    var estadoInput = document.getElementById('id_estado');
    var municipioInput = document.querySelector('[data-municipio-field]');

    if (!estadoInput || !municipioInput) return;

    var datalistId = municipioInput.getAttribute('list');
    var datalist = document.getElementById(datalistId);
    var data = window.__municipiosPorEstado || {};

    function updateMunicipios() {
        var estado = estadoInput.value.trim().toUpperCase();
        var municipios = data[estado] || [];
        datalist.innerHTML = municipios.map(function (m) {
            return '<option value="' + m + '">';
        }).join('');
    }

    estadoInput.addEventListener('input', updateMunicipios);
    estadoInput.addEventListener('change', updateMunicipios);
    updateMunicipios();
});
