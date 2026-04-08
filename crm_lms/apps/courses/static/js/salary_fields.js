function toggleSalaryFields(salaryType) {
    // Скрываем все поля зарплаты
    const priceField = document.getElementById('id_price');
    const hourlyRateField = document.getElementById('id_hourly_rate');
    const salaryPercentageField = document.getElementById('id_salary_percentage');
    
    // Находим родительские div для полей
    const priceParent = priceField ? priceField.closest('.mb-3') : null;
    const hourlyRateParent = hourlyRateField ? hourlyRateField.closest('.mb-3') : null;
    const salaryPercentageParent = salaryPercentageField ? salaryPercentageField.closest('.mb-3') : null;
    
    // Скрываем все поля
    if (priceParent) priceParent.style.display = 'none';
    if (hourlyRateParent) hourlyRateParent.style.display = 'none';
    if (salaryPercentageParent) salaryPercentageParent.style.display = 'none';
    
    // Показываем нужные поля в зависимости от типа
    switch(salaryType) {
        case 'hourly':
            if (hourlyRateParent) {
                hourlyRateParent.style.display = 'block';
                hourlyRateField.setAttribute('required', 'required');
            }
            if (priceField) priceField.removeAttribute('required');
            if (salaryPercentageField) salaryPercentageField.removeAttribute('required');
            break;
            
        case 'percentage':
            if (salaryPercentageParent) {
                salaryPercentageParent.style.display = 'block';
                salaryPercentageField.setAttribute('required', 'required');
            }
            if (priceField) priceField.removeAttribute('required');
            if (hourlyRateField) hourlyRateField.removeAttribute('required');
            break;
            
        case 'monthly':
            if (priceParent) {
                priceParent.style.display = 'block';
                priceField.setAttribute('required', 'required');
            }
            if (hourlyRateField) hourlyRateField.removeAttribute('required');
            if (salaryPercentageField) salaryPercentageField.removeAttribute('required');
            break;
            
        case 'course':
            if (priceParent) {
                priceParent.style.display = 'block';
                priceField.setAttribute('required', 'required');
            }
            if (hourlyRateField) hourlyRateField.removeAttribute('required');
            if (salaryPercentageField) salaryPercentageField.removeAttribute('required');
            break;
            
        default:
            // По умолчанию показываем только цену
            if (priceParent) {
                priceParent.style.display = 'block';
                priceField.setAttribute('required', 'required');
            }
            if (hourlyRateField) hourlyRateField.removeAttribute('required');
            if (salaryPercentageField) salaryPercentageField.removeAttribute('required');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const salaryTypeField = document.getElementById('id_salary_type');
    if (salaryTypeField) {
        // Вызываем функцию при загрузке
        toggleSalaryFields(salaryTypeField.value);
    }
});

// Для совместимости с Django admin
if (typeof django !== 'undefined' && django.jQuery) {
    django.jQuery(document).ready(function() {
        const salaryTypeField = django.jQuery('#id_salary_type');
        if (salaryTypeField.length) {
            toggleSalaryFields(salaryTypeField.val());
            salaryTypeField.on('change', function() {
                toggleSalaryFields(django.jQuery(this).val());
            });
        }
    });
}
