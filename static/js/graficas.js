document.addEventListener("DOMContentLoaded", function () {
    const labels = datos.map(d => d.fecha_hora);

    const crearGrafico = (idCanvas, etiqueta, campo, color) => {
        const valores = datos.map(d => d[campo]);
        const ctx = document.getElementById(idCanvas).getContext("2d");
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels.reverse(),
                datasets: [{
                    label: etiqueta,
                    data: valores.reverse(),
                    borderColor: color,
                    backgroundColor: color + "33",
                    fill: true,
                    tension: 0.3,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    x: { display: true },
                    y: { beginAtZero: false }
                }
            }
        });
    };

    crearGrafico("graficoTemperatura", "Temperatura (°C)", "temperatura", "#f44336");
    crearGrafico("graficoHumedad", "Humedad (%)", "humedad", "#2196f3");
    crearGrafico("graficoPresion", "Presión (hPa)", "presion", "#4caf50");
    crearGrafico("graficoCalidadAire", "Calidad del Aire", "calidad_aire", "#ff9800");
    crearGrafico("graficoRadiacionUV", "Radiación UV", "radiacion_uv", "#9c27b0");
});
