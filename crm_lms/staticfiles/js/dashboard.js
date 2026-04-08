/* ===== CRM LMS — Dashboard Charts ===== */

document.addEventListener('DOMContentLoaded', function () {

    // ── Admin Dashboard ──────────────────────────────────────────────────────
    const studentCtx = document.getElementById('studentsChart');
    if (studentCtx && typeof chartStudentsLabels !== 'undefined') {
        new Chart(studentCtx, {
            type: 'bar',
            data: {
                labels: chartStudentsLabels,
                datasets: [{
                    label: 'Новые студенты',
                    data: chartStudentsData,
                    backgroundColor: 'rgba(99, 102, 241, 0.8)',
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const financeCtx = document.getElementById('financeChart');
    if (financeCtx && typeof chartFinanceLabels !== 'undefined') {
        new Chart(financeCtx, {
            type: 'line',
            data: {
                labels: chartFinanceLabels,
                datasets: [
                    {
                        label: 'Доход',
                        data: chartIncomeData,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.08)',
                        tension: 0.4,
                        fill: true,
                    },
                    {
                        label: 'Расход',
                        data: chartExpenseData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.06)',
                        tension: 0.4,
                        fill: true,
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,.05)' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    // ── Reports – leads sources doughnut ────────────────────────────────────
    const leadsCtx = document.getElementById('leadsSourceChart');
    if (leadsCtx && typeof leadsLabels !== 'undefined') {
        new Chart(leadsCtx, {
            type: 'doughnut',
            data: {
                labels: leadsLabels,
                datasets: [{
                    data: leadsData,
                    backgroundColor: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'],
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } },
                cutout: '65%'
            }
        });
    }

});
