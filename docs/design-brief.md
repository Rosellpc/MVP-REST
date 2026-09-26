Antes de continuar quiero que agregemos un cocepto y sistema de diseño claro, para lo cual quiero que leas este promt, en consecuencia modifiques lo ya contruido hasta ahora, según al concepto y depués de ello añadas esa información valiosa al archivo README.md o crees otro archivo según veas lo más conveniente para el proyecto. También, tengas claro que estaremos implementado TailwindCSS y CSS para los estilos.  Una última cosa, para efectos practicos trae desde internet lo asset de multimedia, para empezar:Actúa como un Senior Product Designer, Design Systems Architect y Frontend Engineer especializado en interfaces premium, React, TypeScript, accesibilidad y diseño de materiales translúcidos con propiedades ópticas físicamente plausibles. 

PROYECTO: RESTAURANTOS

Diseña e implementa un sistema de diseño integral para RestaurantOS, una plataforma Full Stack de gestión de restaurantes que integra autoservicio, recepción de pedidos en cocina y barra, inventario, recetas estandarizadas, costeo y analítica de negocio.

OBJETIVO VISUAL

Crear una experiencia digital elegante, minimalista, sofisticada, silenciosa y funcional, inspirada en los principios visuales de Liquid Glass de Apple, sin copiar su identidad de marca ni depender de sus componentes propietarios.

La interfaz debe transmitir precisión, calma, confianza y calidad profesional. Debe sentirse como un producto digital premium y contemporáneo, no como un dashboard convencional con efectos de glassmorphism aplicados indiscriminadamente.

No utilizar colores fuertes, neón, gradientes saturados, sombras agresivas ni contrastes cromáticos innecesarios.

1\. FILOSOFÍA DEL DISEÑO

El contenido tiene prioridad sobre la decoración.

Utiliza una composición limpia, abundante espacio negativo, tipografía precisa, jerarquía visual clara, geometría consistente y una profundidad espacial sutil.

Aplica superficies translúcidas exclusivamente donde aporten contexto, continuidad espacial o diferenciación entre niveles de interfaz.

El efecto de vidrio debe comportarse como un material óptico, no simplemente como un rectángulo semitransparente con desenfoque.

No utilizar vidrio en todos los componentes. Combinar superficies sólidas, materiales translúcidos y fondos neutros para mantener un equilibrio visual.

2\. PROPIEDADES ÓPTICAS DEL MATERIAL

Implementa materiales inspirados en vidrio real mediante técnicas de renderizado web.

Considera estas propiedades:

\- Transmisión parcial de luz: el fondo debe permanecer perceptible a través de las superficies transparentes.
\- Refracción contextual: cuando sea técnicamente viable, aplicar una distorsión óptica muy sutil y localizada del contenido situado detrás del vidrio.
\- Reflexión especular: representar pequeños reflejos suaves dependientes de la iluminación y, opcionalmente, del movimiento del puntero.
\- Reflejos de Fresnel: intensificar discretamente la reflexión cerca de los bordes del material cuando la implementación lo permita.
\- Desenfoque de fondo: utilizar backdrop-filter de manera moderada y con diferentes intensidades según la elevación del componente.
\- Dispersión visual: representar una difusión suave de la luz sin crear halos cromáticos intensos.
\- Espesor aparente: utilizar bordes delicados, iluminación de contorno y sombras de contacto para transmitir volumen.
\- Integración contextual: adaptar la luminosidad y apariencia de la superficie a su entorno.
\- Movimiento coherente: los reflejos y transiciones deben responder suavemente a los cambios de estado y desplazamiento.

IMPORTANTE: CSS con backdrop-filter, transparencias, sombras y gradientes solo permite aproximar algunas propiedades ópticas del vidrio. No debe afirmarse que produce refracción física real.

Si se necesita una simulación óptica avanzada, valorar WebGL o shaders para componentes específicos, utilizando muestreo del fondo, normales y distorsión localizada. No introducir WebGL de forma global ni sacrificar el rendimiento por fidelidad visual.

Priorizar el rendimiento en dispositivos táctiles, pantallas de cocina y equipos de gama media.

3\. PALETA CROMÁTICA

Crear una paleta neutra, cálida y de baja saturación.

Paleta inicial sugerida:

Background primary: #F7F7F5
Background secondary: #F0F0ED
Surface solid: #FFFFFF
Text primary: #242521
Text secondary: #676963
Border subtle: #DEDFDA
Accent neutral: #777C73

Utilizar blancos cálidos, grises piedra, tonos marfil, grafito suave y matices minerales discretos.

Evitar azul eléctrico, verde fluorescente, rojo saturado, violeta intenso y gradientes multicolor.

Los colores semánticos para errores, advertencias, confirmaciones y estados de pedidos deben ser discretos, pero distinguibles, con contraste suficiente para accesibilidad.

Nunca utilizar únicamente el color para comunicar un estado.

4\. TIPOGRAFÍA

Utilizar una familia tipográfica sans-serif contemporánea, legible y de apariencia refinada.

Priorizar la tipografía de sistema y considerar Inter como alternativa.

Definir una escala tipográfica consistente para:

\- Display
\- Heading XL
\- Heading LG
\- Heading MD
\- Body
\- Body Small
\- Label
\- Caption
\- Numeric KPI

Utilizar pesos moderados y evitar el uso excesivo de negritas.

Los datos numéricos del dashboard deben contar con cifras tabulares.

Utilizar una altura de línea generosa en textos descriptivos y una composición más compacta en indicadores operativos.

5\. ESPACIADO Y GEOMETRÍA

Establecer una escala de espaciado basada en unidades de 4 px.

Utilizar un sistema consistente de radios de borde, tamaños de iconos, alturas de controles y elevaciones.

Preferir esquinas suavemente redondeadas, evitando formas excesivamente circulares en tablas, tarjetas operativas y paneles de alta densidad.

El diseño debe funcionar en desktop, tablet y pantallas táctiles de autoservicio.

6\. COMPONENTES DEL SISTEMA

Diseñar componentes reutilizables para:

\- Button
\- IconButton
\- Input
\- Select
\- Textarea
\- Checkbox
\- RadioGroup
\- Switch
\- Card
\- GlassPanel
\- Modal
\- Dialog
\- Drawer
\- Sidebar
\- Navbar
\- Tabs
\- Badge
\- StatusIndicator
\- Toast
\- Tooltip
\- Dropdown
\- Table
\- DataGrid
\- KPI Card
\- Chart Container
\- Product Card
\- Order Card
\- Production Ticket
\- Inventory Movement Row
\- Quantity Selector
\- Cart Summary

Cada componente debe definir variantes, tamaños, estados interactivos, comportamiento responsive y criterios de accesibilidad.

7\. INTERFAZ DE AUTOSERVICIO

Diseñar una experiencia táctil extremadamente intuitiva.

El cliente debe poder consultar el menú, seleccionar productos, personalizar platos, modificar cantidades, revisar el carrito, confirmar el pedido y consultar su estado sin asistencia de un mesero.

Priorizar fotografías de productos, legibilidad de precios, navegación evidente y botones táctiles amplios.

El lenguaje visual debe transmitir una experiencia gastronómica premium sin reducir la velocidad de interacción.

Las acciones principales deben distinguirse con contraste y jerarquía, no mediante colores saturados.

8\. INTERFAZ DE COCINA Y BARRA

Diseñar un Kitchen Display System de alta legibilidad.

Los pedidos deben poder identificarse rápidamente mediante número, hora, estación, productos, cantidades, modificaciones, alergias declaradas y estado de producción.

Utilizar superficies sólidas o de alta opacidad para los tickets operativos.

No aplicar desenfoque o refracción a textos críticos.

Los estados Pending, In Progress, Ready y Cancelled deben distinguirse mediante texto, iconos, composición y señales cromáticas discretas.

Diseñar controles grandes, visibles y accesibles para uso táctil.

La eficiencia operativa y la seguridad alimentaria tienen prioridad sobre la estética.

9\. INVENTARIO Y KARDEX

Crear una interfaz ordenada, profesional y orientada a datos.

Incluir tablas de movimientos, existencias, unidades de medida, costos unitarios, costos totales, mermas, ajustes, transferencias y alertas de reposición.

Priorizar alineación numérica, filtros comprensibles, búsqueda rápida y visualización clara de ingresos y salidas.

Evitar efectos de vidrio dentro de tablas extensas.

10\. DASHBOARD ADMINISTRATIVO

Diseñar una interfaz ejecutiva, minimalista y analítica.

Incluir áreas para ventas, ticket promedio, pedidos, tiempos de producción, food cost, beverage cost, margen bruto, inventario y variaciones entre consumo teórico y real.

Utilizar gráficos sobrios, escalas claras, etiquetas legibles y una jerarquía de información que facilite la interpretación de indicadores.

No utilizar gráficos 3D decorativos, exceso de sombras ni colores llamativos.

11\. MOVIMIENTO E INTERACCIÓN

Aplicar animaciones suaves, breves y funcionales.

Utilizar cambios sutiles de elevación, opacidad, reflejo y escala.

Evitar efectos elásticos exagerados y movimientos continuos innecesarios.

Respetar prefers-reduced-motion.

Las animaciones nunca deben retrasar una acción crítica, especialmente durante la recepción y preparación de pedidos.

12\. ACCESIBILIDAD

Cumplir WCAG 2.2 AA como objetivo de diseño y validación.

Mantener contraste adecuado en textos y controles.

No colocar texto de bajo contraste sobre materiales transparentes de luminosidad variable.

Implementar navegación por teclado, foco visible, semántica HTML, etiquetas accesibles y objetivos táctiles apropiados.

Crear alternativas visuales para dispositivos sin soporte de backdrop-filter y para usuarios que reduzcan transparencia o movimiento.

13\. TECNOLOGÍAS

Implementar el sistema utilizando:

React
TypeScript
Tailwind CSS
CSS Custom Properties
React Router
Lucide Icons

Utilizar WebGL o shaders únicamente cuando exista una necesidad óptica concreta y justificable.

Definir design tokens independientes de los componentes.

Separar los componentes base del sistema de diseño de los componentes específicos del dominio RestaurantOS.

14\. ENTREGABLES

Generar:

\- Documento de principios visuales.
\- Paleta cromática y tokens semánticos.
\- Escala tipográfica.
\- Sistema de espaciado, geometría y elevación.
\- Definición de materiales translúcidos.
\- Biblioteca de componentes reutilizables.
\- Variantes y estados de los componentes.
\- Layouts para las cuatro interfaces.
\- Implementación responsive.
\- Estados de carga, error, vacío y éxito.
\- Guía de accesibilidad y rendimiento.
\- Ejemplos de implementación en React y TypeScript.

El resultado debe ser un sistema de diseño consistente, escalable, mantenible y visualmente refinado, en el que las propiedades ópticas se utilicen con intención y la funcionalidad operativa siempre tenga prioridad.