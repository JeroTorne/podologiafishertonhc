/*
 * Entrevista por voz para la historia clínica.
 *
 * Recorre las preguntas una por una: las lee en voz alta, escucha la respuesta
 * por el micrófono y completa el campo del formulario que corresponde. La idea
 * es que se pueda usar sin tocar el teclado, porque durante la revisación las
 * manos están ocupadas.
 *
 * Nada se guarda solo: al terminar quedan los campos completados y marcados en
 * amarillo para revisar antes de apretar Guardar.
 */

document.addEventListener('DOMContentLoaded', function () {
    const panel = document.getElementById('entrevista-voz');
    const botonIniciar = document.getElementById('iniciar-entrevista');
    if (!panel || !botonIniciar) {
        return;
    }

    const Reconocimiento = window.SpeechRecognition || window.webkitSpeechRecognition;

    const elementos = {
        progreso: document.getElementById('ev-progreso'),
        barra: document.getElementById('ev-barra'),
        pregunta: document.getElementById('ev-pregunta'),
        estado: document.getElementById('ev-estado'),
        escuchado: document.getElementById('ev-escuchado'),
        resultado: document.getElementById('ev-resultado'),
        candidatos: document.getElementById('ev-candidatos'),
        vozAlta: document.getElementById('ev-voz-alta'),
        diagnostico: document.getElementById('ev-diagnostico'),
        log: document.getElementById('ev-log'),
    };

    let pasos = [];
    let indice = 0;
    let reconocimiento = null;
    let escuchando = false;
    let activa = false;
    let procesando = false;
    let temporizador = null;
    let textoAcumulado = '';

    // ------------------------------------------------------------------
    // Diagnóstico
    // ------------------------------------------------------------------

    // Deja constancia de cada evento del micrófono. Sirve para saber en qué
    // eslabón se corta cuando la entrevista dice "Escuchando" y no reacciona:
    // sin "audiostart" el micrófono no llegó a abrirse (permiso pendiente),
    // con "audiostart" pero sin "soundstart" no entra sonido (micrófono mudo o
    // equivocado), y con "speechstart" pero sin "result" el problema está en
    // la conexión con el servicio de reconocimiento de Google.
    function registrar(texto) {
        // También a la consola, así se puede ver con F12 sin abrir el panel.
        console.log('[entrevista] ' + texto);
        if (!elementos.log) {
            return;
        }
        const hora = new Date().toLocaleTimeString('es-AR', { hour12: false });
        const linea = document.createElement('div');
        linea.textContent = hora + '  ' + texto;
        elementos.log.appendChild(linea);
        elementos.log.scrollTop = elementos.log.scrollHeight;
    }

    // ------------------------------------------------------------------
    // Utilidades del formulario
    // ------------------------------------------------------------------

    function camposDe(nombre) {
        return document.querySelectorAll('[name="' + nombre + '"]');
    }

    function valorActual(nombre) {
        const campos = camposDe(nombre);
        return campos.length ? campos[0].value : null;
    }

    function resaltar(nombre) {
        const campos = camposDe(nombre);
        if (!campos.length) {
            return;
        }
        const contenedor = campos[0].closest('.pie-type');
        if (contenedor) {
            contenedor.classList.add('completado-por-voz');
        }
    }

    function aplicarValores(paso, valores) {
        const campos = camposDe(paso.campo);
        if (!campos.length) {
            return;
        }

        if (paso.tipo === 'opciones') {
            campos.forEach(function (input) {
                input.checked = valores.indexOf(input.value) !== -1;
            });
        } else {
            campos[0].value = valores.length ? valores[0] : '';
            campos[0].dispatchEvent(new Event('change', { bubbles: true }));
            // El proyecto carga select2, que necesita el evento de jQuery.
            if (window.jQuery) {
                window.jQuery(campos[0]).trigger('change');
            }
        }
        resaltar(paso.campo);
    }

    // ------------------------------------------------------------------
    // Voz
    // ------------------------------------------------------------------

    function hablar(texto, alTerminar) {
        const leerEnVozAlta = elementos.vozAlta && elementos.vozAlta.checked;
        if (!leerEnVozAlta || !window.speechSynthesis) {
            alTerminar();
            return;
        }

        let yaSiguio = false;
        function seguir() {
            if (!yaSiguio) {
                yaSiguio = true;
                alTerminar();
            }
        }

        // Si quedó algo sonando, lo cortamos: si no, el micrófono se escucha a sí mismo.
        window.speechSynthesis.cancel();
        const frase = new SpeechSynthesisUtterance(texto);
        frase.lang = 'es-AR';
        frase.rate = 1.05;
        frase.onend = seguir;
        frase.onerror = seguir;
        window.speechSynthesis.speak(frase);

        // Chrome a veces no dispara onend y la entrevista quedaría colgada
        // esperando para siempre. Este margen la destraba sola.
        setTimeout(seguir, 1500 + texto.length * 90);
    }

    function escuchar() {
        if (!activa || escuchando || procesando) {
            return;
        }
        const paso = pasos[indice];
        reconocimiento.continuous = paso.tipo === 'texto';
        try {
            reconocimiento.start();
            escuchando = true;
            marcarEstado('escuchando', 'Escuchando...');
        } catch (error) {
            // start() tira excepción si ya venía corriendo; lo reintentamos solos.
            escuchando = false;
            registrar('start() rechazado: ' + (error.message || error.name));
        }
    }

    function dejarDeEscuchar() {
        if (reconocimiento && escuchando) {
            escuchando = false;
            reconocimiento.abort();
        }
    }

    function marcarEstado(clase, texto) {
        elementos.estado.className = 'ev-estado ev-' + clase;
        elementos.estado.textContent = texto;
    }

    // ------------------------------------------------------------------
    // Recorrido de las preguntas
    // ------------------------------------------------------------------

    function seOmite(paso) {
        if (!paso.omitir_si) {
            return false;
        }
        const valor = valorActual(paso.omitir_si.campo);
        return paso.omitir_si.valores.indexOf(valor) !== -1;
    }

    function mostrarPaso() {
        cancelarAvance();
        dejarDeEscuchar();
        procesando = false;

        // Saltamos las preguntas que ya no vienen al caso: si dijo que no tiene
        // diabetes, no tiene sentido preguntar qué medicación toma.
        while (indice < pasos.length && seOmite(pasos[indice])) {
            indice += 1;
        }
        if (indice >= pasos.length) {
            terminar();
            return;
        }

        const paso = pasos[indice];
        textoAcumulado = '';
        elementos.progreso.textContent = 'Pregunta ' + (indice + 1) + ' de ' + pasos.length;
        elementos.barra.style.width = ((indice / pasos.length) * 100) + '%';
        elementos.pregunta.textContent = paso.pregunta;
        elementos.escuchado.textContent = '';
        elementos.resultado.textContent = '';
        elementos.resultado.className = 'ev-resultado';
        elementos.candidatos.innerHTML = '';

        marcarEstado('leyendo', 'Leyendo la pregunta...');
        hablar(paso.pregunta, escuchar);
    }

    function avanzar() {
        indice += 1;
        mostrarPaso();
    }

    function retroceder() {
        indice = Math.max(0, indice - 1);
        mostrarPaso();
    }

    function cancelarAvance() {
        if (temporizador) {
            clearTimeout(temporizador);
            temporizador = null;
        }
    }

    function programarAvance() {
        cancelarAvance();
        temporizador = setTimeout(avanzar, 2200);
    }

    // ------------------------------------------------------------------
    // Qué hacer con lo que se escuchó
    // ------------------------------------------------------------------

    function procesar(texto) {
        const paso = pasos[indice];
        // Mientras esperamos la respuesta no volvemos a escuchar: si no, el
        // micrófono puede pisar la respuesta anterior con ruido de fondo.
        procesando = true;
        marcarEstado('pensando', 'Interpretando...');

        fetch(panel.dataset.interpretarUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify({ campo: paso.campo, texto: texto }),
        })
            .then(function (respuesta) { return respuesta.json(); })
            .then(function (datos) {
                procesando = false;
                if (!datos.ok) {
                    marcarEstado('error', datos.mensaje || 'No se pudo interpretar.');
                    return;
                }
                if (datos.comando) {
                    ejecutarComando(datos.comando);
                    return;
                }
                aplicarResultado(paso, datos, texto);
            })
            .catch(function () {
                procesando = false;
                marcarEstado('error', 'Se cortó la conexión con el servidor.');
                escuchar();
            });
    }

    function ejecutarComando(comando) {
        if (comando === 'siguiente' || comando === 'saltear') {
            avanzar();
        } else if (comando === 'atras') {
            retroceder();
        } else if (comando === 'repetir') {
            mostrarPaso();
        } else if (comando === 'terminar') {
            terminar();
        }
    }

    function aplicarResultado(paso, datos, textoCrudo) {
        if (paso.tipo === 'texto') {
            textoAcumulado = (textoAcumulado + ' ' + textoCrudo).trim();
            aplicarValores(paso, [textoAcumulado]);
            elementos.resultado.className = 'ev-resultado ev-ok';
            elementos.resultado.textContent = textoAcumulado;
            marcarEstado('escuchando', 'Seguí dictando, o decí "siguiente" para continuar.');
            return;
        }

        if (datos.confianza === 'nula') {
            elementos.resultado.className = 'ev-resultado ev-duda';
            elementos.resultado.textContent = 'No entendí. Repetilo o elegí una opción:';
            mostrarCandidatos(paso, datos.candidatos);
            marcarEstado('duda', 'Esperando');
            escuchar();
            return;
        }

        aplicarValores(paso, datos.valores);
        const leido = datos.textos.length ? datos.textos.join(', ') : 'Ninguna';

        if (datos.confianza === 'media') {
            // No estamos seguros: lo dejamos puesto pero sin avanzar solo.
            elementos.resultado.className = 'ev-resultado ev-duda';
            elementos.resultado.textContent = 'Entendí "' + leido + '". ¿Está bien?';
            mostrarCandidatos(paso, datos.candidatos);
            marcarEstado('duda', 'Confirmá diciendo "siguiente" o elegí otra');
            escuchar();
            return;
        }

        elementos.resultado.className = 'ev-resultado ev-ok';
        elementos.resultado.textContent = leido;
        marcarEstado('ok', 'Anotado');
        programarAvance();
    }

    function mostrarCandidatos(paso, candidatos) {
        elementos.candidatos.innerHTML = '';
        (candidatos || []).forEach(function (candidato) {
            const boton = document.createElement('button');
            boton.type = 'button';
            boton.className = 'ev-candidato';
            boton.textContent = candidato.texto;
            boton.addEventListener('click', function () {
                aplicarValores(paso, [candidato.valor]);
                elementos.resultado.className = 'ev-resultado ev-ok';
                elementos.resultado.textContent = candidato.texto;
                elementos.candidatos.innerHTML = '';
                avanzar();
            });
            elementos.candidatos.appendChild(boton);
        });
    }

    // ------------------------------------------------------------------
    // Arranque y cierre
    // ------------------------------------------------------------------

    function prepararReconocimiento() {
        reconocimiento = new Reconocimiento();
        reconocimiento.lang = 'es-AR';
        reconocimiento.interimResults = true;
        reconocimiento.maxAlternatives = 1;

        // Estos cuatro no hacen nada salvo dejar rastro de hasta dónde llegó.
        reconocimiento.onstart = function () { registrar('start (reconocimiento iniciado)'); };
        reconocimiento.onaudiostart = function () { registrar('audiostart (micrófono abierto)'); };
        reconocimiento.onsoundstart = function () { registrar('soundstart (entra sonido)'); };
        reconocimiento.onspeechstart = function () { registrar('speechstart (se detecta voz)'); };

        reconocimiento.onresult = function (evento) {
            let parcial = '';
            for (let i = evento.resultIndex; i < evento.results.length; i += 1) {
                const alternativa = evento.results[i][0].transcript;
                if (evento.results[i].isFinal) {
                    registrar('result final: "' + alternativa.trim() + '"');
                    procesar(alternativa.trim());
                } else {
                    parcial += alternativa;
                }
            }
            if (parcial) {
                elementos.escuchado.textContent = parcial;
            }
        };

        // Ningún error puede quedar mudo: si no mostramos nada, el panel se
        // queda en "Escuchando..." y parece colgado aunque el micrófono esté
        // bien. Los que no cortan la entrevista dejan que onend reintente.
        const MENSAJES_ERROR = {
            'not-allowed': ['Hay que permitir el micrófono en el navegador.', true],
            'service-not-allowed': ['El navegador bloqueó el servicio de voz.', true],
            'audio-capture': ['No se pudo abrir el micrófono. ¿Lo está usando otro programa?', true],
            'network': ['Sin conexión con el servicio de voz de Google. Reintentando...', false],
            'no-speech': ['No se escuchó nada. Probá de nuevo.', false],
            'bad-grammar': ['El navegador rechazó la configuración de voz.', true],
            'language-not-supported': ['El navegador no tiene el español disponible.', true],
        };

        reconocimiento.onerror = function (evento) {
            escuchando = false;
            registrar('error: ' + evento.error);

            // Lo disparamos nosotros al cambiar de pregunta, no es una falla.
            if (evento.error === 'aborted') {
                return;
            }

            const conocido = MENSAJES_ERROR[evento.error];
            const texto = conocido ? conocido[0] : ('Error del micrófono: ' + evento.error);
            const corta = conocido ? conocido[1] : true;

            marcarEstado(corta ? 'error' : 'duda', texto);
            if (corta) {
                activa = false;
            }
        };

        reconocimiento.onend = function () {
            escuchando = false;
            registrar('end (reconocimiento terminado)');
            // Chrome corta solo cada tanto: si la entrevista sigue abierta, no
            // estamos esperando el avance automático y no hay nada en curso,
            // volvemos a escuchar. Mientras se lee la pregunta no, porque si no
            // el micrófono se escucha a sí mismo.
            if (activa && !temporizador && !procesando && !hablando()) {
                setTimeout(escuchar, 250);
            }
        };
    }

    function hablando() {
        return !!(window.speechSynthesis
            && (window.speechSynthesis.speaking || window.speechSynthesis.pending));
    }

    function iniciar() {
        if (!Reconocimiento) {
            alert('La entrevista por voz necesita Google Chrome o Microsoft Edge. '
                + 'En este navegador no está disponible.');
            return;
        }

        // Pedimos el micrófono de forma explícita antes de arrancar. Si no lo
        // hacemos y el cartel de permiso de Chrome se cierra sin contestar, el
        // reconocimiento arranca igual, no da ningún error y la entrevista se
        // queda diciendo "Escuchando..." para siempre.
        permitirMicrofono().then(cargarGuion).catch(function (motivo) {
            alert('No se pudo usar el micrófono: ' + motivo + '.\n\n'
                + 'Tocá el ícono de la cámara o el candado en la barra de '
                + 'direcciones, poné el micrófono en "Permitir" y recargá la página.');
        });
    }

    function permitirMicrofono() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            return Promise.resolve();
        }
        return navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function (flujo) {
                // El audio en sí no nos sirve: el reconocimiento abre el suyo.
                // Lo pedimos solo para que el permiso quede resuelto.
                flujo.getTracks().forEach(function (pista) { pista.stop(); });
                registrar('permiso de micrófono concedido');
            })
            .catch(function (error) {
                registrar('permiso de micrófono rechazado: ' + error.name);
                if (error.name === 'NotAllowedError') {
                    throw 'el permiso está denegado o quedó sin contestar';
                }
                if (error.name === 'NotFoundError') {
                    throw 'no hay ningún micrófono conectado';
                }
                throw error.message || error.name;
            });
    }

    function cargarGuion() {
        return fetch(panel.dataset.guionUrl)
            .then(function (respuesta) { return respuesta.json(); })
            .then(function (datos) {
                pasos = datos.pasos;
                indice = 0;
                activa = true;
                panel.classList.add('abierto');
                document.body.classList.add('entrevista-abierta');
                if (!reconocimiento) {
                    prepararReconocimiento();
                }
                mostrarPaso();
            })
            .catch(function () {
                alert('No se pudo cargar el cuestionario. Revisá la conexión.');
            });
    }

    function terminar() {
        activa = false;
        cancelarAvance();
        dejarDeEscuchar();
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        panel.classList.remove('abierto');
        document.body.classList.remove('entrevista-abierta');

        const aviso = document.getElementById('ev-aviso');
        if (aviso) {
            aviso.style.display = 'block';
            aviso.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    // ------------------------------------------------------------------
    // Botones
    // ------------------------------------------------------------------

    botonIniciar.addEventListener('click', iniciar);

    if (elementos.diagnostico) {
        elementos.diagnostico.addEventListener('change', function () {
            elementos.log.classList.toggle('visible', elementos.diagnostico.checked);
        });
    }
    document.getElementById('ev-repetir').addEventListener('click', mostrarPaso);
    document.getElementById('ev-atras').addEventListener('click', retroceder);
    document.getElementById('ev-saltear').addEventListener('click', avanzar);
    document.getElementById('ev-terminar').addEventListener('click', terminar);

    document.addEventListener('keydown', function (evento) {
        if (!activa) {
            return;
        }
        if (evento.key === 'Escape') {
            terminar();
        } else if (evento.key === 'ArrowRight') {
            avanzar();
        } else if (evento.key === 'ArrowLeft') {
            retroceder();
        }
    });
});
