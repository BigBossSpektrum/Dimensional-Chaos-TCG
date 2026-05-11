/**
 * SweetAlert2 personalizado con fondo fondoDC.png
 * Componente reutilizable para mostrar alertas en toda la app.
 *
 * Uso: showSwalAlert(tag, message, bgImageUrl)
 *   - tag: 'error' | 'success' | 'warning' | 'info'
 *   - message: texto del mensaje
 *   - bgImageUrl: URL de la imagen de fondo (fondoDC.png)
 *
 * Uso: showSwalAlertList(tag, messages, bgImageUrl)
 *   - tag: 'error' | 'success' | 'warning' | 'info'
 *   - messages: array de mensajes (se muestra como lista si son múltiples)
 *   - bgImageUrl: URL de la imagen de fondo (fondoDC.png)
 */
function showSwalAlert(tag, message, bgImageUrl) {
    const isError = tag === 'error';
    const isSuccess = tag === 'success';
    const isWarning = tag === 'warning';

    Swal.fire({
        icon: isError ? 'error' : isSuccess ? 'success' : isWarning ? 'warning' : 'info',
        title: isError ? 'Error' : isSuccess ? '¡Éxito!' : isWarning ? 'Advertencia' : 'Aviso',
        text: message,
        confirmButtonText: 'Aceptar',
        background: 'url("' + bgImageUrl + '") center/cover no-repeat',
        color: '#fff',
        confirmButtonColor: isError ? '#d33' : isSuccess ? '#28a745' : '#3085d6',
        customClass: {
            popup: 'swal-custom-popup',
            title: 'swal-custom-title',
            htmlContainer: 'swal-custom-text',
            confirmButton: 'swal-custom-btn'
        },
        backdrop: 'rgba(0,0,0,0.7)'
    });
}

function showSwalAlertList(tag, messagesArr, bgImageUrl) {
    if (messagesArr.length === 1) {
        showSwalAlert(tag, messagesArr[0], bgImageUrl);
        return;
    }

    const isError = tag === 'error';
    const isSuccess = tag === 'success';
    const isWarning = tag === 'warning';

    var htmlContent = '<ul style="text-align: left; margin: 0; padding-left: 20px; list-style: none;">';
    messagesArr.forEach(function(msg) {
        htmlContent += '<li style="margin-bottom: 6px; font-size: 14px;">\u26A0\uFE0F ' + msg + '</li>';
    });
    htmlContent += '</ul>';

    Swal.fire({
        icon: isError ? 'error' : isSuccess ? 'success' : isWarning ? 'warning' : 'info',
        title: isError ? 'Error' : isSuccess ? '¡Éxito!' : isWarning ? 'Advertencia' : 'Aviso',
        html: htmlContent,
        confirmButtonText: 'Aceptar',
        background: 'url("' + bgImageUrl + '") center/cover no-repeat',
        color: '#fff',
        confirmButtonColor: isError ? '#d33' : isSuccess ? '#28a745' : '#3085d6',
        customClass: {
            popup: 'swal-custom-popup',
            title: 'swal-custom-title',
            htmlContainer: 'swal-custom-text',
            confirmButton: 'swal-custom-btn'
        },
        backdrop: 'rgba(0,0,0,0.7)'
    });
}
