/* APEX: cargar como archivo estático de aplicación. */
window.drinkAdvisor = (() => {
    "use strict";

    let base;
    let barId;

    const item = name => apex.item(name);
    const element = id => document.getElementById(id);
    const node = (tag, text) => {
        const result = document.createElement(tag);
        result.textContent = text;
        return result;
    };

    function configurar(url) {
        base = new URL(url).href.replace(/\/+$/, "");
    }

    async function consultar(id, recurso, datos) {
        const respuesta = await fetch(`${base}/bares/${id}/${recurso}`, datos && {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(datos)
        });
        if (!respuesta.ok) {
            throw new Error(`HTTP ${respuesta.status}`);
        }
        return respuesta.json();
    }

    function promedio(comentarios) {
        const notas = comentarios.map(c => c.calificacion)
            .filter(nota => Number.isInteger(nota) && nota >= 1 && nota <= 5);
        return notas.length
            ? `★ ${(notas.reduce((suma, nota) => suma + nota, 0) / notas.length).toFixed(1)}`
            : "Sin calificaciones";
    }

    async function cargarCards() {
        const solicitudes = new Map();
        await Promise.all([...document.querySelectorAll(".cal-bar")].map(async etiqueta => {
            const id = Number(etiqueta.dataset.bar);
            if (!Number.isSafeInteger(id) || id <= 0) return;
            if (!solicitudes.has(id)) {
                solicitudes.set(id, consultar(id, "comentarios"));
            }
            try {
                etiqueta.textContent = promedio(await solicitudes.get(id));
            } catch {
                etiqueta.textContent = "Calificación no disponible";
            }
        }));
    }

    function fechaVisible(fecha) {
        if (!fecha) return "";
        const instante = new Date(fecha);
        return Number.isNaN(instante.getTime()) ? "" : instante.toLocaleString("es-CO", {
            dateStyle: "medium", timeStyle: "short", timeZone: "America/Bogota"
        });
    }

    function comentarioVisible(comentario) {
        const tarjeta = node("article", "");
        tarjeta.className = "da-entry";
        const cabecera = node("header", "");
        cabecera.append(node("strong", comentario.autor || "Anónimo"));
        if (comentario.calificacion) cabecera.append(node("span", `★ ${comentario.calificacion}/5`));
        const fecha = fechaVisible(comentario.fecha || comentario.date);
        if (fecha) cabecera.append(node("span", fecha));
        tarjeta.append(cabecera, node("p", comentario.texto));
        return tarjeta;
    }

    function eventoVisible(evento) {
        const { _id, nombre, bar_id, fecha_creacion, ...campos } = evento;
        const tarjeta = node("article", "");
        tarjeta.className = "da-entry";
        tarjeta.append(node("h3", nombre || "Evento"));
        const fecha = fechaVisible(fecha_creacion);
        if (fecha) tarjeta.append(node("p", fecha));
        const etiquetas = {
            artista: "Artista", cover: "Cover", cupos: "Cupos",
            descuento: "Descuento", hora_inicio: "Hora de inicio", hora_fin: "Hora de fin"
        };
        const lista = node("dl", "");
        for (const [campo, valor] of Object.entries(campos)) {
            const etiqueta = Object.hasOwn(etiquetas, campo) ? etiquetas[campo] : campo.replaceAll("_", " ");
            const texto = valor !== null && typeof valor === "object" ? JSON.stringify(valor) : String(valor);
            lista.append(node("dt", etiqueta), node("dd", texto));
        }
        if (lista.children.length) tarjeta.append(lista);
        return tarjeta;
    }

    async function cargar(recurso, dibujar, vacio) {
        const contenedor = element(`${recurso}-container`);
        const resumen = recurso === "comentarios" ? element("promedio-bar") : null;
        try {
            const datos = await consultar(barId, recurso);
            if (resumen) resumen.textContent = promedio(datos);
            contenedor.replaceChildren(...(datos.length ? datos.map(dibujar) : [node("p", vacio)]));
        } catch {
            if (resumen) resumen.textContent = "Calificación no disponible";
            contenedor.replaceChildren(node("p", `No fue posible cargar ${recurso}.`));
        }
    }

    const cargarComentarios = () => cargar("comentarios", comentarioVisible, "Aún no hay comentarios.");
    const cargarEventos = () => cargar("eventos", eventoVisible, "Aún no hay eventos.");

    function error(mensaje) {
        apex.message.showErrors([{ type: "error", location: "page", message: mensaje, unsafe: false }]);
    }

    async function guardar(boton, recurso, datos, refrescar, limpiar, mensaje) {
        if (!barId || boton.disabled) return;
        boton.disabled = true;
        try {
            apex.message.clearErrors();
            await consultar(barId, recurso, datos);
            limpiar();
            apex.message.showPageSuccess(mensaje);
            await refrescar();
        } catch {
            error(`No fue posible guardar en ${recurso}. Intenta de nuevo.`);
        } finally {
            boton.disabled = false;
        }
    }

    function enviarComentario(boton) {
        const texto = item("P3_TEXTO").getValue().trim();
        const calificacion = item("P3_CALIFICACION").getValue();
        if (!texto) return error("Escribe un comentario.");
        const datos = { bar_id: barId, texto, autor: apex.env.APP_USER };
        if (calificacion !== "") datos.calificacion = Number(calificacion);
        return guardar(boton, "comentarios", datos, cargarComentarios, () => {
            item("P3_TEXTO").setValue("");
            item("P3_CALIFICACION").setValue("");
        }, "Comentario guardado.");
    }

    const camposEvento = {
        concierto: { P3_ARTISTA: "artista", P3_COVER: "cover" },
        happy_hour: { P3_DESCUENTO: "descuento", P3_HORA_INICIO: "hora_inicio" }
    };

    function mostrarCamposEvento() {
        const tipo = item("P3_TIPO_EVENTO").getValue();
        for (const [grupo, campos] of Object.entries(camposEvento)) {
            for (const nombre of Object.keys(campos)) {
                if (grupo === tipo) item(nombre).show();
                else item(nombre).hide();
            }
        }
    }

    function enviarEvento(boton) {
        const nombre = item("P3_NOMBRE_EVENTO").getValue().trim();
        const tipo = item("P3_TIPO_EVENTO").getValue();
        if (!nombre) return error("Escribe el nombre del evento.");
        const datos = { nombre };
        const campos = Object.hasOwn(camposEvento, tipo) ? camposEvento[tipo] : {};
        for (const [itemId, campo] of Object.entries(campos)) {
            const valor = item(itemId).getValue().trim();
            if (valor === "") continue;
            if (campo === "cover") {
                const cover = Number(valor);
                if (!Number.isSafeInteger(cover) || cover < 0) {
                    return error("El cover debe ser un entero mayor o igual a cero.");
                }
                datos[campo] = cover;
            } else if (campo === "hora_inicio" && !/^([01]\d|2[0-3]):[0-5]\d$/.test(valor)) {
                return error("Escribe la hora en formato HH:MM.");
            } else {
                datos[campo] = valor;
            }
        }
        return guardar(boton, "eventos", datos, cargarEventos, () => {
            item("P3_NOMBRE_EVENTO").setValue("");
            for (const grupo of Object.values(camposEvento)) {
                for (const campo of Object.keys(grupo)) item(campo).setValue("");
            }
        }, "Evento guardado.");
    }

    function iniciarDetalle() {
        const id = Number(item("P3_BAR_ID").getValue());
        mostrarCamposEvento();
        if (!Number.isSafeInteger(id) || id <= 0) {
            for (const boton of ["ENVIAR_COMENTARIO", "CREAR_EVENTO"]) element(boton).disabled = true;
            return error("Selecciona un bar en la página de bares.");
        }
        barId = id;
        return Promise.all([cargarComentarios(), cargarEventos()]);
    }

    return { configurar, cargarCards, iniciarDetalle, enviarComentario, mostrarCamposEvento, enviarEvento };
})();
