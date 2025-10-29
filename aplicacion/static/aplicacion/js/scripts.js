/*!
* Start Bootstrap - Creative v7.0.7 (https://startbootstrap.com/theme/creative)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-creative/blob/master/LICENSE)
*/
//
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink function
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
            
        }

    };

    // Shrink the navbar 
    navbarShrink();

    // Shrink the navbar when page is scrolled
    document.addEventListener('scroll', navbarShrink);



    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });
});

function toggleMenu() {
    document.querySelector(".lista-nav").classList.toggle("show");
  }


document.addEventListener('DOMContentLoaded', function() {
    const addButton = document.getElementById('agregar-seguimiento');
    const formContainer = document.getElementById('form-seguimiento');
    const cancelButton = document.getElementById('cancelar-seguimiento');
    const fechaInput = document.getElementById('id_fecha_seguimiento');
    
    if (addButton && formContainer) {
        // Establecer fecha de hoy por defecto
        const today = new Date().toISOString().split('T')[0];
        fechaInput.value = today;
        
        addButton.addEventListener('click', function() {
            formContainer.style.display = 'block';
            addButton.style.display = 'none';
        });

        cancelButton.addEventListener('click', function() {
            formContainer.style.display = 'none';
            addButton.style.display = 'block';
            fechaInput.value = today;
            document.getElementById('id_descripcion_seguimiento').value = '';
        });
    }

    // Manejar eliminación de seguimientos
    const deleteButtons = document.querySelectorAll('.btn-sm-danger');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const seguimientoId = this.getAttribute('data-seguimiento-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar este seguimiento?')) {
                // Obtener el token CSRF
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // Hacer petición AJAX para eliminar
                fetch(`/eliminar-seguimiento/${seguimientoId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Recargar la página para actualizar la lista
                        location.reload();
                    } else {
                        alert('Error al eliminar el seguimiento: ' + (data.message || 'Error desconocido'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al eliminar el seguimiento');
                });
            }
        });
    });
});



