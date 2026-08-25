from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(r"C:\Python\tesis\imagenes")
OUT.mkdir(parents=True, exist_ok=True)
BLUE, GREEN, ORANGE, PURPLE, RED, GRAY = "#1f4e79", "#2e7d32", "#d97706", "#6b4fa1", "#b42318", "#5f6b76"

def font(size, bold=False):
    p = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    try: return ImageFont.truetype(p, size)
    except OSError: return ImageFont.load_default()

def canvas(title, w=2400, h=900):
    im = Image.new("RGB", (w, h), "white"); d = ImageDraw.Draw(im)
    d.text((w//2, 55), title, font=font(38, True), fill="#17202a", anchor="mm")
    return im, d

def box(d, xy, text, fill, outline, fs=23):
    d.rounded_rectangle(xy, radius=24, fill=fill, outline=outline, width=4)
    x1,y1,x2,y2=xy
    d.multiline_text(((x1+x2)//2,(y1+y2)//2), text, font=font(fs), fill="#17202a", anchor="mm", align="center", spacing=7)

def arrow(d, p1, p2, color=GRAY):
    d.line([p1,p2], fill=color, width=5); x,y=p2
    d.polygon([(x,y),(x-18,y-11),(x-18,y+11)], fill=color)

def save(im,name): im.save(OUT/name, quality=96)

im,d=canvas("Trazabilidad del pipeline analítico de la investigación", 2800, 900)
labels=["Fuentes\nVentas · compras\nINPC · clima · calendario","Auditoría y limpieza\nHomologación · fechas\nvalores reales","Dataset maestro\n1,612 días\n65 variables","Ingeniería de características\nRezagos · ventanas\neventos exógenos","Representaciones\nCompleto · reducido\nPCA","Validación temporal\nRolling-Origin\n3 orígenes finales","Modelos y DSS\nComparación contra\nlínea base empírica"]
for i,t in enumerate(labels):
    x=45+i*392; ec=BLUE if i<3 else GREEN if i<6 else ORANGE; fc="#e8f1f8" if i<3 else "#edf6ed" if i<6 else "#fff3dd"
    box(d,(x,260,x+330,550),t,fc,ec,22)
    if i<6: arrow(d,(x+334,405),(x+382,405))
d.text((1400,700),"Principio de control: cada transformación conserva fecha, fuente, cobertura y reglas reproducibles;\nlas características históricas utilizan exclusivamente información anterior al día pronosticado.",font=font(25),fill=GRAY,anchor="mm",align="center",spacing=8)
save(im,"88_pipeline_trazabilidad_tesis.png")

im,d=canvas("Diseño evaluativo: comparación temporal contra la línea base",2400,1000)
box(d,(90,250,530,500),"Datos históricos ordenados\n2022–2026","#e8f1f8",BLUE,25)
box(d,(760,180,1260,380),"Línea base empírica\nÚltimo valor y promedio de 7 días","#fff3dd",ORANGE,24)
box(d,(760,500,1260,730),"Modelos candidatos\nARIMA · SARIMA · regresión\nárboles · RF · RNN/LSTM","#edf6ed",GREEN,24)
box(d,(1580,300,2070,580),"Evaluación Rolling-Origin\nMAE · RMSE · MAPE\npor ventana y promedio","#f0ebf8",PURPLE,25)
box(d,(1580,680,2070,870),"Contraste de H1\nReducción relativa de RMSE\nUmbral: 20%","#fde8e7",RED,24)
arrow(d,(535,365),(750,280)); arrow(d,(535,395),(750,610)); arrow(d,(1265,280),(1570,390)); arrow(d,(1265,610),(1570,490)); d.line([(1825,585),(1825,670)],fill=RED,width=5); d.polygon([(1825,670),(1814,650),(1836,650)],fill=RED)
d.text((1200,925),"Cada modelo aprende del pasado y se evalúa en observaciones futuras no vistas; no se emplea partición aleatoria.",font=font(24),fill=GRAY,anchor="mm")
save(im,"89_diseno_evaluacion_temporal.png")

im,d=canvas("Arquitectura funcional del sistema de soporte a la decisión (DSS)",2500,900)
items=[("Artefactos del pipeline\nExcel · JSON · métricas\nmodelos ganadores",BLUE,"#e8f1f8"),("Capa de integración\nEstructura JavaScript\ntrazabilidad por objetivo",GREEN,"#edf6ed"),("Lógica analítica\nComparación con línea base\nreducción RMSE y H1",PURPLE,"#f0ebf8"),("Interfaz DSS\nFiltros · KPI · ventanas\nlectura ejecutiva",ORANGE,"#fff3dd")]
for i,(t,ec,fc) in enumerate(items):
    x=90+i*610; box(d,(x,250,x+450,530),t,fc,ec,24)
    if i<3: arrow(d,(x+455,390),(x+595,390))
box(d,(820,650,1680,820),"Salvaguarda metodológica: la decisión permanece bajo responsabilidad humana;\nel tablero no actualiza datos automáticamente.","#fde8e7",RED,23)
save(im,"90_arquitectura_funcional_dss.png")

im,d=canvas("Flujo de decisión operativa apoyado por el DSS",2500,850)
labels=["Pronóstico por objetivo\nventas o compras","Revisión de cobertura\ny estabilidad temporal","Comparación contra\nlínea base empírica","Estimación de riesgo\ny requerimiento","Revisión del responsable\ndel negocio","Decisión y registro\noperativo"]
for i,t in enumerate(labels):
    x=65+i*405; ec=BLUE if i<2 else GREEN if i<4 else ORANGE; fc="#e8f1f8" if i<2 else "#edf6ed" if i<4 else "#fff3dd"
    box(d,(x,245,x+315,480),t,fc,ec,22)
    if i<5: arrow(d,(x+320,362),(x+395,362))
d.text((1250,670),"Regla de uso: si la cobertura está desactualizada, el error es inestable o la mejora no supera el umbral,\nel resultado se interpreta como apoyo diagnóstico y no como autorización automática de compra.",font=font(24),fill=GRAY,anchor="mm",align="center",spacing=8)
save(im,"91_flujo_decision_operativa_dss.png")
print("Activos científicos Rev33 generados.")
