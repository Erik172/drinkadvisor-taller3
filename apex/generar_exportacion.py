import sys
from pathlib import Path

raiz = Path(__file__).resolve().parents[1]
base = Path(sys.argv[1]).read_text(encoding="utf-8-sig")
destino = Path(sys.argv[2])
api = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8765"


def q(s):
    return "'" + s.replace("'", "''") + "'"


def leer(nombre):
    return (raiz / "apex" / nombre).read_text(encoding="utf-8").strip()


def id_(n):
    return f"wwv_flow_imp.id({9002856000000000 + n})"


def attrs(**values):
    return "wwv_flow_t_plugin_attributes(wwv_flow_t_varchar2(" + ",".join(
        q(v) for par in values.items() for v in par
    ) + ")).to_clob"


def crear(tipo, numero, **parametros):
    return f"wwv_flow_imp_page.create_{tipo}(\n p_id=>{id_(numero)}" + "".join(
        f"\n,p_{clave}=>{valor}" for clave, valor in parametros.items()
    ) + "\n);\n"


def estatico(n, nombre, mime):
    data = leer(nombre).encode("utf-8").hex().upper()
    return (
        f"prompt --application/shared_components/files/{nombre}\nbegin\n"
        "wwv_flow_imp.g_varchar2_table := wwv_flow_imp.empty_varchar2_table;\n"
        + "".join(f"wwv_flow_imp.g_varchar2_table({i//200+1}) := '{data[i:i+200]}';\n"
                  for i in range(0, len(data), 200))
        + f"wwv_flow_imp_shared.create_app_static_file(\n p_id=>{id_(n)},\n"
        f" p_file_name=>'{nombre}',\n p_mime_type=>'{mime}',\n p_file_charset=>'utf-8',\n"
        " p_file_content=>wwv_flow_imp.varchar2_to_blob(wwv_flow_imp.g_varchar2_table));\nend;\n/\n"
    )


def region(n, titulo, html, orden):
    return crear("page_plug", n, plug_name=q(titulo), plug_template=4073835273271169698,
                 plug_display_sequence=orden, plug_item_display_point="'BELOW'",
                 plug_source=q(leer(html)), attributes=attrs(expand_shortcuts="N", output_as="HTML"))


def item(n, nombre, region_id, titulo, tipo, *, lov=None, nulo=None, limite=None, obligatorio=False):
    extra = {}
    if lov:
        extra.update(lov=q(lov), lov_display_null="'YES'", lov_null_text=q(nulo), lov_display_extra="'NO'")
    if limite:
        extra["cMaxlength"] = limite
    if tipo == "TEXTAREA":
        extra["cHeight"] = 3
    if obligatorio:
        extra["is_required"] = "true"
    return crear("page_item", n, name=q(nombre), item_sequence=n * 10,
                 item_plug_id=id_(region_id), prompt=q(titulo), source_type="'ALWAYS_NULL'",
                 display_as=q("NATIVE_" + tipo), field_template=1610598304472262251,
                 item_template_options="'#DEFAULT#'", **extra)


def boton(n, nombre, region_id, titulo):
    return crear("page_button", n, button_sequence=n*10, button_plug_id=id_(region_id),
                 button_name=q(nombre), static_id=q(nombre), button_action="'DEFINED_BY_DA'",
                 button_template_id=4073839297780169708, button_image_alt=q(titulo),
                 button_template_options="'#DEFAULT#'", button_is_hot="'Y'")


def accion(n, nombre, trigger, codigo, target):
    boton = trigger == "BUTTON"
    destino = {"triggering_button_id": id_(target)} if boton else {"triggering_element": q(target)}
    return crear("page_da_event", n, name=q(nombre), event_sequence=n*10, triggering_element_type=q(trigger),
                 bind_type="'bind'", execution_type="'IMMEDIATE'", bind_event_type=q("click" if boton else "change"),
                 **destino) + crear("page_da_action", n+1, event_id=id_(n), event_result="'TRUE'",
                                    action_sequence=10, execute_on_page_init="'N'",
                                    action="'NATIVE_JAVASCRIPT_CODE'", attributes=attrs(js_code=codigo))


def scripts(metodo):
    codigo = f"drinkAdvisor.configurar('&DA_API_BASE!JS.');\ndrinkAdvisor.{metodo}();"
    if metodo == "cargarCards":
        codigo += '\napex.jQuery("#explorar-bares").on("apexafterrefresh apexcardspagechange", () => drinkAdvisor.cargarCards());'
    return ("\n,p_javascript_file_urls=>'#APP_FILES#drinkadvisor.js'"
            f"\n,p_javascript_code_onload=>{q(codigo)}"
            "\n,p_css_file_urls=>'#APP_FILES#drinkadvisor.css'")


base = base.replace("'DrinkAdvisor_Base_Taller')", "'DrinkAdvisor_Taller_3')", 1)
base = base.replace("'PARRANDEROS-NEW188892')", "'DRINKADVISOR-TALLER-3')", 1)
base = base.replace(",p_substitution_value_01=>'Parranderos New'",
                    ",p_substitution_value_01=>'Parranderos New'\n,p_substitution_string_02=>'DA_API_BASE'\n"
                    f",p_substitution_value_02=>{q(api.rstrip('/'))}", 1)
pos = base.index("prompt --application/shared_components/files/")
base = base[:pos] + estatico(1, "drinkadvisor.js", "text/javascript") + estatico(2, "drinkadvisor.css", "text/css") + base[pos:]
p2, p3, p4 = [base.index(f"prompt --application/pages/page_0000{n}") for n in (2, 3, 4)]
cards = base[p2:p3].replace(",p_step_title=>'Explorar Bares'",
                            ",p_step_title=>'Explorar Bares'" + scripts("cargarCards"), 1)
cards = cards.replace("p_sub_title_html_expr=>'&CIUDAD. - &PRESUPUESTO_SIGNO.'",
                      f"p_sub_title_html_expr=>{q(leer('cards-subtitulo.html'))}", 1)
cards = cards.replace("::&DEBUG.:CR,2:P3_BAR_ID:", "::&DEBUG.:3:P3_BAR_ID:", 1)
detalle = base[p3:p4].replace(",p_name=>'Bebidas del Bar'",
                             ",p_name=>'Detalle del bar'" + scripts("iniciarDetalle"), 1)
partes = crear("report_region", 3, name="'Información del bar'", static_id="'informacion-bar'",
               template=4073835273271169698, display_sequence=52, region_template_options="'#DEFAULT#'",
               component_template_options="'#DEFAULT#'", source_type="'NATIVE_SQL_REPORT'",
               query_type="'SQL'", source=q(leer("detalle.sql")), ajax_enabled="'N'", lazy_loading="false",
               query_row_template=2540130677583398057, query_headings_type="'QUERY_COLUMNS'", query_num_rows=1,
               query_options="'DERIVED_REPORT_COLUMNS'", query_num_rows_type="'SHOW_ALL'")
for seq, (col, titulo) in enumerate([
    ("NOMBRE", "Nombre"), ("CIUDAD", "Ciudad"), ("SEDE_DIRECCION", "Dirección"), ("PRESUPUESTO", "Presupuesto")
], 1):
    partes += crear("report_columns", 3+seq, query_column_id=seq, column_alias=q(col), column_display_sequence=seq*10,
                    column_heading=q(titulo), disable_sort_column="'Y'", derived_column="'N'", include_in_export="'Y'")
partes += region(10, "Comentarios", "comentarios.html", 54) + region(11, "Eventos", "eventos.html", 56)
partes += item(12, "P3_TEXTO", 10, "Comentario", "TEXTAREA", limite=4000)
partes += item(13, "P3_CALIFICACION", 10, "Calificación", "SELECT_LIST",
               lov="STATIC:1;1,2;2,3;3,4;4,5;5", nulo="Sin calificación")
partes += item(14, "P3_NOMBRE_EVENTO", 11, "Nombre del evento", "TEXT_FIELD", limite=200, obligatorio=True)
partes += item(15, "P3_TIPO_EVENTO", 11, "Tipo de evento", "SELECT_LIST",
               lov="STATIC:Concierto;concierto,Happy hour;happy_hour", nulo="General")
partes += item(16, "P3_ARTISTA", 11, "Artista", "TEXT_FIELD", limite=200)
partes += item(17, "P3_COVER", 11, "Cover (COP)", "NUMBER_FIELD")
partes += item(18, "P3_DESCUENTO", 11, "Descuento", "TEXT_FIELD", limite=200)
partes += item(19, "P3_HORA_INICIO", 11, "Hora de inicio (HH:MM)", "TEXT_FIELD", limite=5)
partes += boton(20, "ENVIAR_COMENTARIO", 10, "Enviar comentario") + boton(21, "CREAR_EVENTO", 11, "Registrar evento")
partes += accion(31, "Enviar comentario", "BUTTON", "drinkAdvisor.enviarComentario(this.triggeringElement);", 20)
partes += accion(33, "Registrar evento", "BUTTON", "drinkAdvisor.enviarEvento(this.triggeringElement);", 21)
partes += accion(35, "Campos por tipo de evento", "ITEM", "drinkAdvisor.mostrarCamposEvento();", "P3_TIPO_EVENTO")
fin = detalle.rindex("end;")
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(base[:p2] + cards + detalle[:fin] + partes + detalle[fin:] + base[p4:], encoding="utf-8")
