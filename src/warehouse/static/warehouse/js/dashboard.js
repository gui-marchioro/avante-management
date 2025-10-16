document.addEventListener('DOMContentLoaded', function () {
    const itemsDataElement = document.getElementById('items-data');
    if (!itemsDataElement) {
        return;
    }

    const itemsData = JSON.parse(itemsDataElement.textContent);

    if (itemsData.length === 0) {
        return;
    }

    // Parse market_value as float
    itemsData.forEach(item => {
        item.market_value = parseFloat(item.market_value);
    });

    // Calculate totals
    const totalQuantity = itemsData.reduce((sum, item) => sum + item.quantity, 0);
    const totalMarketValue = itemsData.reduce((sum, item) => sum + (item.quantity * item.market_value), 0);

    document.getElementById('total-quantity').textContent = totalQuantity;
    document.getElementById('total-market-value').textContent = 'R$' + totalMarketValue.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    // Item Type Chart (Pie)
    const typeCounts = itemsData.reduce((acc, item) => {
        acc[item.type] = (acc[item.type] || 0) + item.quantity;
        return acc;
    }, {});

    const itemTypeCtx = document.getElementById('item-type-chart').getContext('2d');
    new Chart(itemTypeCtx, {
        type: 'pie',
        data: {
            labels: Object.keys(typeCounts),
            datasets: [{
                label: 'Quantidade por Tipo',
                data: Object.values(typeCounts),
                backgroundColor: [
                    'rgba(255, 99, 132, 0.8)',
                    'rgba(54, 162, 235, 0.8)',
                    'rgba(255, 206, 86, 0.8)',
                    'rgba(75, 192, 192, 0.8)',
                    'rgba(153, 102, 255, 0.8)',
                    'rgba(255, 159, 64, 0.8)'
                ],
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: 'Quantidade por Tipo'
                }
            }
        }
    });

    // Manufacturer Chart (Bar)
    const manufacturerCounts = itemsData.reduce((acc, item) => {
        acc[item.manufacturer] = (acc[item.manufacturer] || 0) + item.quantity;
        return acc;
    }, {});

    const manufacturerCtx = document.getElementById('manufacturer-chart').getContext('2d');
    new Chart(manufacturerCtx, {
        type: 'bar',
        data: {
            labels: Object.keys(manufacturerCounts),
            datasets: [{
                label: 'Quantidade por Fabricante',
                data: Object.values(manufacturerCounts),
                backgroundColor: 'rgba(75, 192, 192, 0.8)',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: 'Quantidade por Fabricante'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
});