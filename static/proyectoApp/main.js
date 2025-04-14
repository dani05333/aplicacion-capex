function listadoCategoria() {
    $.ajax({
        url: "/tabla_categoria_nuevo/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_categorias')) {
                $('#tabla_categorias').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            var table = $('#tabla_categorias').DataTable({
                data: response,
                columns: [
                    { 
                        data: null,
                        orderable: false,
                        className: 'select-checkbox',
                        defaultContent: '',
                        render: function(data, type, row) {
                            return `<input type="checkbox" class="select-row" data-id="${row.id}">`;
                        }
                    },
                    { data: "id" },
                    { data: "nombre" },
                    { data: "proyecto" },
                    { data: "id_padre" },
                    { data: "categoria_relacionada"
                     },
                    { data: "nivel" },
                    { data: "final" },
                    { data: "total_costo",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-categoria/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-categoria btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });

            // Manejar selección/deselección de todas las casillas
            $('#select-all').on('click', function() {
                var isChecked = $(this).prop('checked');
                $('.select-row').prop('checked', isChecked);
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

$(document).ready(function () {
    listadoCategoria();
    
    // Manejar eliminación masiva
    $('#eliminar-seleccionados').on('click', function() {
        var selectedIds = [];
        $('.select-row:checked').each(function() {
            selectedIds.push($(this).data('id'));
        });

        if (selectedIds.length === 0) {
            alert("Por favor selecciona al menos una categoría para eliminar.");
            return;
        }

        if (confirm(`¿Estás seguro de que deseas eliminar las ${selectedIds.length} categorías seleccionadas?`)) {
            $.ajax({
                url: "/eliminar-categorias-masivo/",  // Nueva ruta para eliminación masiva
                type: "POST",
                data: { ids: selectedIds },
                headers: { "X-CSRFToken": getCSRFToken() },
                success: function (response) {
                    if (response.success) {
                        alert(`${selectedIds.length} categorías eliminadas correctamente.`);
                        listadoCategoria(); // Recargar listado
                        $('#select-all').prop('checked', false); // Desmarcar "Seleccionar todo"
                    } else {
                        alert("Error al eliminar: " + response.error);
                    }
                },
                error: function () {
                    alert("Error al procesar la solicitud.");
                }
            });
        }
    });
});

$(document).on("click", ".btn-eliminar-categoria", function () {
    let categoriaId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar esta categoría?")) {
        $.ajax({
            url: "/eliminar-categoria/",  // Ruta para eliminar la categoría
            type: "POST",
            data: { id: categoriaId },
            headers: { "X-CSRFToken": getCSRFToken() }, // Token CSRF para Django
            success: function (response) {
                if (response.success) {
                    alert("Categoría eliminada correctamente.");
                    listadoCategoria(); // Recargar listado después de eliminar
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token (necesario para Django)
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoAdquisiciones() {
    $.ajax({
        url: "/tabla_adquisiciones/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_adquisiciones')) {
                $('#tabla_adquisiciones').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_adquisiciones').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "tipo_origen" },
                    { data: "tipo_categoria" },
                    { data: "costo_unitario",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "crecimiento",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "flete",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_con_flete",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-adquisicion/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-adquisicion btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoAdquisiciones();
});

// ✅ Evento para eliminar adquisiciones
$(document).on("click", ".btn-eliminar-adquisicion", function () {
    let adquisicionId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar esta adquisición?")) {
        $.ajax({
            url: "/eliminar-adquisicion/",
            type: "POST",
            data: { id: adquisicionId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Adquisición eliminada correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoAdquisiciones();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});



// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}




//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoEquiposConstruccion() {
    $.ajax({
        url: "/tabla_equipos_construccion/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            if ($.fn.DataTable.isDataTable('#tabla_equipos_construccion')) {
                $('#tabla_equipos_construccion').DataTable().destroy();
            }
            
            $('#tabla_equipos_construccion').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "horas_maquina_unidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_maquina_hora",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_horas_maquina",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-equipo-construccion/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-equipo-construccion btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

$(document).ready(function () {
    listadoEquiposConstruccion();
});

// ✅ Manejar clic en el botón eliminar
$(document).on("click", ".btn-eliminar-equipo", function () {
    let equipoId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este equipo?")) {
        $.ajax({
            url: "/eliminar-equipo-construccion/",
            type: "POST",
            data: { id: equipoId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Equipo eliminado correctamente.");
                    listadoEquiposConstruccion();  // Recargar la tabla
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token en Django
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}




////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoManoObra() {
    $.ajax({
        url: "/tabla_mano_obra/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            if ($.fn.DataTable.isDataTable('#tabla_mano_obra')) {
                $('#tabla_mano_obra').DataTable().destroy();
            }
            
            $('#tabla_mano_obra').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },  // ✅ Mostrar nombre en lugar de ID
                    { data: "horas_hombre_unidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "fp",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "rendimiento",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },  // ✅ Nuevo campo
                    { data: "horas_hombre_final",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },  // ✅ Nuevo campo calculado
                    { data: "cantidad_horas_hombre",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },  // ✅ Nuevo campo calculado
                    { data: "costo_hombre_hora",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "tarifas_usd_hh_mod",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "tarifa_usd_hh_equipos",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_hh",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd_mod",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd_equipos",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },  // ✅ Nuevo cálculo
                    
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-mano-obra/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-mano-obra btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

$(document).ready(function () {
    listadoManoObra();
});

// ✅ Manejar clic en el botón eliminar
$(document).on("click", ".btn-eliminar-mano", function () {
    let manoObraId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro de mano de obra?")) {
        $.ajax({
            url: "/eliminar-mano-obra/",
            type: "POST",
            data: { id: manoObraId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    listadoManoObra();  // Recargar la tabla
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token en Django
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}




/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoMaterialesOtros() {
    $.ajax({
        url: "/tabla_materiales_otros/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_materiales_otros')) {
                $('#tabla_materiales_otros').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_materiales_otros').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "costo_unidad",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "crecimiento",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    
                    { 
                        data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                    },
                    { data: "fletes",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }    
                     },
                    { data: "total_sitio",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-material-otro/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-material btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                    
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

$(document).ready(function () {
    listadoMaterialesOtros();
});

$(document).on("click", ".btn-eliminar-material", function () {
    let materialId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este material?")) {
        $.ajax({
            url: "/eliminar-material/",
            type: "POST",
            data: { id: materialId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Material eliminado correctamente.");

                    // ✅ En lugar de `ajax.reload()`, volvemos a llamar a `listadoMaterialesOtros()`
                    listadoMaterialesOtros();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});


// ✅ Función para obtener el CSRF Token (para evitar problemas con Django)
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoEspecificoCategoria() {
    $.ajax({
        url: "/tabla_especifico_categoria/", // Asegúrate de crear esta URL en Django
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_especifico_categoria')) {
                $('#tabla_especifico_categoria').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_especifico_categoria').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "unidad" },
                    { data: "cantidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "dedicacion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "duracion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-especifico-categoria/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-especifico btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Llamar a la función al cargar la página
$(document).ready(function () {
    listadoEspecificoCategoria();
});

// ✅ Manejar la eliminación de un elemento
$(document).on("click", ".btn-eliminar-especifico", function () {
    let especificoId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este elemento?")) {
        $.ajax({
            url: "/eliminar-especifico/",
            type: "POST",
            data: { id: especificoId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Elemento eliminado correctamente.");
                    listadoEspecificoCategoria(); // ✅ Recargar la tabla
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////7

function listadoStaffEnami() {
    $.ajax({
        url: "/tabla_staff_enami/",  // Asegúrate de configurar la URL en Django
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_staff_enami')) {
                $('#tabla_staff_enami').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_staff_enami').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "categoria" },
                    { data: "nombre" },
                    { data: "valor",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "dotacion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "duracion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "factor_utilizacion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_horas_hombre",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-staff-enami/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-staff btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Llamar a la función al cargar la página
$(document).ready(function () {
    listadoStaffEnami();
});

$(document).on("click", ".btn-eliminar-staff", function () {
    let staffId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este elemento?")) {
        $.ajax({
            url: "/eliminar-staff-enami/",
            type: "POST",
            data: { id: staffId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Elemento eliminado correctamente.");
                    listadoStaffEnami(); // ✅ Recargar la tabla
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}



function listadoCantidades() {
    $.ajax({
        url: "/tabla_cantidades/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_cantidades')) {
                $('#tabla_cantidades').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_cantidades').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "unidad_medida" },
                    { data: "cantidad",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "fc",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "cantidad_final",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-cantidad/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-cantidad btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoCantidades();
});

// ✅ Evento para eliminar cantidades
$(document).on("click", ".btn-eliminar-cantidad", function () {
    let cantidadId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar esta cantidad?")) {
        $.ajax({
            url: "/eliminar-cantidad/",
            type: "POST",
            data: { id: cantidadId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Cantidad eliminada correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoCantidades();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listadoContratoSubcontrato() {
    $.ajax({
        url: "/tabla_contrato_subcontrato/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_contrato_subcontrato')) {
                $('#tabla_contrato_subcontrato').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_contrato_subcontrato').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "costo_laboral_indirecto_usd_hh",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd_indirectos_contratista",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "usd_por_unidad",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "fc_subcontrato",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "usd_total_subcontrato",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_contrato_total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_contrato_unitario",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-contrato-subcontrato/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-contrato btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página

$(document).ready(function () {
    listadoContratoSubcontrato();
});

// ✅ Evento para eliminar contratos/subcontratos
$(document).on("click", ".btn-eliminar-contrato", function () {
    let contratoId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este contrato/subcontrato?")) {
        $.ajax({
            url: "/eliminar-contrato-subcontrato/",
            type: "POST",
            data: { id: contratoId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Contrato eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoContratoSubcontrato();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////


function listadoCotizacionMateriales() {
    $.ajax({
        url: "/tabla_cotizacion_materiales/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_cotizacion_materiales')) {
                $('#tabla_cotizacion_materiales').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_cotizacion_materiales').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "tipo_suministro" },
                    { data: "tipo_moneda" },
                    { data: "pais_entrega" },
                    { data: "fecha_cotizacion_referencia" },
                    { data: "cotizacion_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "cotizacion_clp",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "factor_correccion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "moneda_aplicada",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "flete_unitario",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "origen_precio" },
                    { data: "cotizacion" },
                    { data: "moneda_origen" },
                    { data: "tasa_cambio",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-cotizacion-materiales/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-cotizacion btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoCotizacionMateriales();
});

// ✅ Evento para eliminar cotizaciones
$(document).on("click", ".btn-eliminar-cotizacion", function () {
    let cotizacionId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar esta cotización?")) {
        $.ajax({
            url: "/eliminar-cotizacion-materiales/",
            type: "POST",
            data: { id: cotizacionId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Cotización eliminada correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoCotizacionMateriales();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listadoIngenieriaDetallesContraparte() {
    $.ajax({
        url: "/tabla_ingenieria_detalles_contraparte/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_ingenieria_detalles_contraparte')) {
                $('#tabla_ingenieria_detalles_contraparte').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_ingenieria_detalles_contraparte').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "nombre" },
                    { data: "UF",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "MB" },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-ingenieria-detalles-contraparte/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-ingenieria btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoIngenieriaDetallesContraparte();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-ingenieria", function () {
    let ingenieriaId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-ingenieria-detalles-contraparte/",
            type: "POST",
            data: { id: ingenieriaId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoIngenieriaDetallesContraparte();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function listadoGestionPermisos() {
    $.ajax({
        url: "/tabla_gestion_permisos/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_gestion_permisos')) {
                $('#tabla_gestion_permisos').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_gestion_permisos').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "nombre" },
                    { data: "dedicacion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "meses",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL').format(data)}`;
                        }
                     },
                    { data: "cantidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL').format(data)}`;
                        }
                     },
                    { data: "turno" },
                    { data: "MB" },
                    { data: "HH",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-gestion-permisos/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-permiso btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoGestionPermisos();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-permiso", function () {
    let permisoId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-gestion-permisos/",
            type: "POST",
            data: { id: permisoId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoGestionPermisos();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function listadoDueno() {
    $.ajax({
        url: "/tabla_dueno/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_dueno')) {
                $('#tabla_dueno').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_dueno').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "nombre" },
                    { data: "total_hh",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_hh_us",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-dueno/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-dueno btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoDueno();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-dueno", function () {
    let duenoId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-dueno/",
            type: "POST",
            data: { id: duenoId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoDueno();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function listadoMB() {
    $.ajax({
        url: "/tabla_mb/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_mb')) {
                $('#tabla_mb').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_mb').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "mb",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "fc",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "anio" },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-mb/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-mb btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoMB();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-mb", function () {
    let mbId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-mb/",
            type: "POST",
            data: { id: mbId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoMB();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function listadoAdministracionSupervision() {
    $.ajax({
        url: "/tabla_administracion_supervision/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_administracion_supervision')) {
                $('#tabla_administracion_supervision').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_administracion_supervision').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "unidad" },
                    { data: "precio_unitario_clp",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_unitario",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "factor_uso",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "cantidad_u_persona",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "mb_seleccionado",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_clp",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_us",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_mb",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-administracion-supervision/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-administracion-supervision btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoAdministracionSupervision();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-administracion-supervision", function () {
    let adminSupId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-administracion-supervision/",
            type: "POST",
            data: { id: adminSupId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoAdministracionSupervision();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}



function listadoPersonalIndirectoContratista() {
    $.ajax({
        url: "/tabla_personal_indirecto_contratista/",
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_personal_indirecto_contratista')) {
                $('#tabla_personal_indirecto_contratista').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_personal_indirecto_contratista').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "mb_seleccionado" },
                    { data: "turno" },
                    { data: "unidad" },
                    { data: "hh_mes",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "plazo_mes",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "total_hh",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "precio_unitario_clp_hh",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "tarifa_usd_hh",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_clp",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_us",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total_mb",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-personal-indirecto-contratista/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-personal-indirecto-contratista btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoPersonalIndirectoContratista();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-personal-indirecto-contratista", function () {
    let personalId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-personal-indirecto-contratista/",
            type: "POST",
            data: { id: personalId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoPersonalIndirectoContratista();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}



function listadoServiciosApoyo() {
    $.ajax({
        url: "/tabla_servicios_apoyo/",  // Endpoint to fetch data
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destroy previous instance of DataTable if it exists
            if ($.fn.DataTable.isDataTable('#tabla_servicios_apoyo')) {
                $('#tabla_servicios_apoyo').DataTable().destroy();
            }
            
            // ✅ Initialize DataTable with the correct data
            $('#tabla_servicios_apoyo').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "unidad" },
                    { data: "cantidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "hh_totales",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "tarifas_clp",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "mb" },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-servicios-apoyo/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-servicios-apoyo btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoServiciosApoyo();
});

// ✅ Event for deleting records
$(document).on("click", ".btn-eliminar-servicios-apoyo", function () {
    let servicioId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-servicios-apoyo/",  // Endpoint to delete the entry
            type: "POST",
            data: { id: servicioId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Reload the table after deletion
                    listadoServiciosApoyo();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Function to get the CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


function listadoOtrosADM() {
    $.ajax({
        url: "/tabla_otros_adm/",  // Cambia esta URL si es necesario
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_otros_adm')) {
                $('#tabla_otros_adm').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_otros_adm').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "HH",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "MB" },
                    { data: "total_usd",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "dedicacion",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "meses",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL').format(data)}`;
                        }
                     },
                    { data: "cantidad",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "turno" },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-otros-adm/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-otros-adm btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoOtrosADM();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-otros-adm", function () {
    let otrosAdmId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-otros-adm/",  // Cambia esta URL si es necesario
            type: "POST",
            data: { id: otrosAdmId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoOtrosADM();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listadoAdministrativoFinanciero() {
    $.ajax({
        url: "/tabla_administrativo_financiero/",  // Cambia esta URL si es necesario
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_administrativo_financiero')) {
                $('#tabla_administrativo_financiero').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_administrativo_financiero').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "unidad" },
                    { data: "valor",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "meses",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL').format(data)}`;
                        }
                     },
                    { data: "sobre_contrato_base",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "costo_total",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-administrativo-financiero/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-administrativo-financiero btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoAdministrativoFinanciero();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-administrativo-financiero", function () {
    let administrativoFinancieroId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-administrativo-financiero/",  // Cambia esta URL si es necesario
            type: "POST",
            data: { id: administrativoFinancieroId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoAdministrativoFinanciero();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listadoDatosEP() {
    $.ajax({
        url: "/tabla_datos_ep/",  // Cambia esta URL si es necesario
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // ✅ Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_datos_ep')) {
                $('#tabla_datos_ep').DataTable().destroy();
            }
            
            // ✅ Inicializar DataTable con los datos correctos
            $('#tabla_datos_ep').DataTable({
                data: response,
                columns: [
                    { data: "id" },
                    { data: "id_categoria" },
                    { data: "hh_profesionales",
                        render: function (data) {
                            return `${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "precio_hh",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<a href="/editar-datos-ep/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-datos-ep btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                }
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
        }
    });
}

// ✅ Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoDatosEP();
});

// ✅ Evento para eliminar registros
$(document).on("click", ".btn-eliminar-datos-ep", function () {
    let datosEPId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro?")) {
        $.ajax({
            url: "/eliminar-datos-ep/",  // Cambia esta URL si es necesario
            type: "POST",
            data: { id: datosEPId },
            headers: { "X-CSRFToken": getCSRFToken() },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    
                    // ✅ Recargar la tabla después de eliminar
                    listadoDatosEP();
                } else {
                    alert("Error al eliminar: " + response.error);
                }
            },
            error: function () {
                alert("Error al procesar la solicitud.");
            }
        });
    }
});

// ✅ Función para obtener el CSRF Token
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}


//////////////////////////////////////////////////////////////////////////////////////////////////////////////////

function listadoDatosOtrosEP() {
    $.ajax({
        url: "/tabla_datos_otros_ep/",  // Asegúrate de tener esta URL configurada en tus urls.py
        type: "GET",
        dataType: "json",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        success: function(response) {
            // Destruir instancia previa de DataTable si existe
            if ($.fn.DataTable.isDataTable('#tabla_datos_otros_ep')) {
                $('#tabla_datos_otros_ep').DataTable().destroy();
            }
            
            // Inicializar DataTable con los datos
            $('#tabla_datos_otros_ep').DataTable({
                data: response,
                columns: [
                    { data: "id", },
                    { 
                        data: "id_categoria", 
                        
                    },
                    { data: "comprador", title: "Comprador",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "dedicacion", title: "Dedicación",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "plazo", title: "Plazo",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "sueldo_pax", title: "Sueldo Pax",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "gestiones", title: "Gestión",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { data: "viajes", title: "Viajes",
                        render: function (data) {
                            return `$${new Intl.NumberFormat('es-CL', { minimumFractionDigits: 2 }).format(data)}`;
                        }
                     },
                    { 
                        data: null, 
                        title: "Editar",
                        render: function(data, type, row) {
                            return `<a href="/editar-datos-otros-ep/${row.id}/" class="btn btn-warning btn-sm">Editar</a>`;
                        }
                    },
                    { 
                        data: null, 
                        title: "Eliminar",
                        render: function(data, type, row) {
                            return `<button class="btn-eliminar-datos-otros-ep btn btn-danger btn-sm" data-id="${row.id}">Eliminar</button>`;
                        }
                    }
                ],
                language: {
                    search: "Buscar:",
                    lengthMenu: "Mostrar _MENU_ entradas",
                    info: "Mostrando _START_ a _END_ de _TOTAL_ entradas",
                    paginate: {
                        first: "Primero",
                        last: "Último",
                        next: "Siguiente",
                        previous: "Anterior"
                    }
                },
                dom: 'Bfrtip',  // Para botones de exportación si los necesitas
                buttons: [
                    'copy', 'csv', 'excel', 'pdf', 'print'
                ]
            });
        },
        error: function(xhr, status, error) {
            console.error("Error en la petición AJAX:", error);
            alert("Error al cargar los datos. Por favor, recarga la página.");
        }
    });
}

// Cargar la tabla al iniciar la página
$(document).ready(function () {
    listadoDatosOtrosEP();
});

// Evento para eliminar registros de DatosOtrosEP
$(document).on("click", ".btn-eliminar-datos-otros-ep", function () {
    let datosId = $(this).data("id");

    if (confirm("¿Estás seguro de que deseas eliminar este registro de Otros EP?")) {
        $.ajax({
            url: "/eliminar-datos-otros-ep/",  // Asegúrate de tener esta URL configurada
            type: "POST",
            data: { 
                id: datosId,
                csrfmiddlewaretoken: getCSRFToken() 
            },
            success: function (response) {
                if (response.success) {
                    alert("Registro eliminado correctamente.");
                    // Recargar la tabla después de eliminar
                    listadoDatosOtrosEP();
                } else {
                    alert("Error al eliminar: " + (response.error || "Error desconocido"));
                }
            },
            error: function (xhr) {
                alert("Error en la solicitud: " + (xhr.responseJSON?.error || "Error de conexión"));
            }
        });
    }
});

// Función para obtener el CSRF Token (la misma que ya tenías)
function getCSRFToken() {
    return document.cookie.split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
}