/**
 * SweetAlert2 personalizado con fondo fondoDC.png
 * Componente reutilizable para mostrar alertas en toda la app.
 *
 * Uso: showSwalAlert(tag, message, bgImageUrl)
 *   - tag: 'error' | 'success' | 'warning' | 'info'
 *   - message: texto del mensaje
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
