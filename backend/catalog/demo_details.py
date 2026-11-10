"""Fictional catalog content for a practice menu, never a recipe declaration."""

NOTICE = "DEMOSTRACIÓN:"
ALLERGEN_NOTICE = (
    "DEMOSTRACIÓN: "
    "No es una declaración verificada. "
)

# kcal, carbohydrate (g), protein (g), fat (g), example serving.
PROFILES = {
    "cocktail": (180, 22, 0, 0, "200 ml"),
    "starter": (350, 32, 15, 18, "250 g"),
    "pasta": (480, 55, 18, 21, "300 g"),
    "soup": (280, 28, 15, 12, "350 ml"),
    "vegetable": (380, 45, 12, 17, "300 g"),
    "main": (650, 60, 35, 30, "400 g"),
    "dessert": (320, 42, 6, 14, "150 g"),
    "coffee": (5, 1, 0, 0, "150 ml"),
    "milk_coffee": (120, 12, 6, 5, "200 ml"),
    "infusion": (2, 0, 0, 0, "250 ml, sin azúcar"),
    "juice": (120, 30, 0, 0, "300 ml"),
    "water": (0, 0, 0, 0, "300 ml"),
    "beer": (145, 12, 1, 0, "330 ml"),
}

# SKU, expected current name, description, hypothetical ingredients, allergens, profile.
# Names guard against applying these examples to the older, different seed menu.
ROWS = [
    ("CAMPO-CA-001", "Matacuy Sour", "Cóctel cítrico de inspiración andina, con un final herbal y una espuma suave.", "Pisco; infusión de matacuy; zumo de limón; jarabe de azúcar; clara de huevo; hielo", ["Huevo"], "cocktail"),
    ("CAMPO-CA-002", "Inti Let", "Combinación refrescante de fruta tropical, cítricos y un toque de especias.", "Pisco; zumo de maracuyá; zumo de naranja; jarabe de canela; hielo", [], "cocktail"),
    ("CAMPO-CA-003", "Capitán Jora", "Cóctel de carácter intenso que combina notas de cereal y hierbas aromáticas.", "Pisco; bebida de maíz de jora; vermut rojo; jarabe simple; hielo", ["Sulfitos"], "cocktail"),
    ("CAMPO-CA-004", "Emoliente Mule", "Bebida especiada y burbujeante con jengibre y un fondo herbal.", "Pisco; infusión de cebada; jengibre; limón; agua con gas; azúcar; hielo", ["Gluten"], "cocktail"),
    ("CAMPO-CA-005", "Frutillada", "Cóctel frutal de fresa con un equilibrio dulce y cítrico.", "Pisco; fresas; zumo de limón; jarabe de azúcar; hielo", [], "cocktail"),
    ("CAMPO-CA-006", "Campo Punch", "Ponche tropical de aroma fresco, pensado para una presentación colorida.", "Pisco; zumo de piña; naranja; limón; jarabe de azúcar; hielo", [], "cocktail"),
    ("CAMPO-CA-007", "Andean Bird", "Cóctel de fruta tropical con notas herbales y un ligero amargor.", "Ron; zumo de piña; aperitivo amargo; limón; jarabe simple; hielo", [], "cocktail"),
    ("CAMPO-CA-008", "Muyu", "Cóctel cremoso de fruta y semillas con un final suave y aromático.", "Pisco; pulpa de lúcuma; leche; jarabe de sésamo; hielo", ["Lácteos", "Sésamo"], "cocktail"),
    ("CAMPO-CC-001", "Pisco Sour clásico", "Clásico cóctel de pisco y limón, con espuma y un toque de amargo.", "Pisco; zumo de limón; jarabe de azúcar; clara de huevo; amargo aromático; hielo", ["Huevo"], "cocktail"),
    ("CAMPO-CC-002", "Chicha Sour", "Versión frutal del sour con notas de maíz morado y especias.", "Pisco; chicha morada; limón; jarabe de azúcar; clara de huevo; hielo", ["Huevo"], "cocktail"),
    ("CAMPO-CC-003", "Chilcano", "Cóctel largo de pisco, limón y jengibre, servido bien frío.", "Pisco; ginger ale; zumo de limón; hielo", [], "cocktail"),
    ("CAMPO-CC-004", "Pisco Punch", "Cóctel de piña y pisco con una terminación cítrica y refrescante.", "Pisco; zumo de piña; limón; jarabe de azúcar; hielo", [], "cocktail"),
    ("CAMPO-PC-001", "Musuq pacha", "Entrada de vegetales y granos andinos con una crema suave y hierbas frescas.", "Quinua; papa; zanahoria; queso fresco; yogur; hierbas; aceite de oliva", ["Lácteos"], "starter"),
    ("CAMPO-PC-002", "Pacha mama", "Selección de tubérculos y legumbres acompañada de una salsa cremosa de frutos secos.", "Papa; camote; altramuz cocido; cacahuetes; ají amarillo; cebolla; limón; aceite", ["Cacahuetes", "Altramuz"], "starter"),
    ("CAMPO-PC-003", "Inca light", "Ensalada fresca de quinua y vegetales con un aliño cítrico de mostaza.", "Quinua; lechuga; tomate; pepino; palta; mostaza; limón; aceite de oliva", ["Mostaza"], "starter"),
    ("CAMPO-PC-004", "Machu picchu", "Bocados dorados de papa y queso con una crema de ají de intensidad suave.", "Papa; queso fresco; harina de trigo; huevo; ají amarillo; leche; aceite", ["Gluten", "Huevo", "Lácteos"], "starter"),
    ("CAMPO-PC-005", "Trilogia andina", "Tres preparaciones de tubérculos andinos, presentadas con salsas y semillas.", "Papa; olluco; oca; queso fresco; crema de leche; sésamo; hierbas; sal", ["Lácteos", "Sésamo"], "starter"),
    ("CAMPO-EN-001", "Fettuccine frutti delle ande", "Pasta larga con una salsa cremosa y una selección de productos del mar.", "Pasta de trigo; huevo; camarones; mejillones; crema de leche; ajo; perejil", ["Gluten", "Crustáceos", "Huevo", "Lácteos", "Moluscos"], "pasta"),
    ("CAMPO-EN-002", "Anticucho de corazón", "Brochetas de corazón marinadas con ají y especias, acompañadas de papa.", "Corazón de res; ají panca; ajo; comino; vinagre de vino; papa; aceite", ["Sulfitos"], "starter"),
    ("CAMPO-EN-003", "Causita cusqueña", "Capas de papa sazonada con ají y limón, con un relleno cremoso.", "Papa amarilla; pollo; palta; mayonesa con huevo; ají amarillo; limón; sal", ["Huevo"], "starter"),
    ("CAMPO-EN-004", "Ravioli", "Pasta rellena de queso y espinaca servida con una salsa suave.", "Harina de trigo; huevo; queso ricota; espinaca; mantequilla; crema de leche", ["Gluten", "Huevo", "Lácteos"], "pasta"),
    ("CAMPO-EN-005", "Ceviche", "Pescado marinado al momento con limón, ají y cebolla, acompañado de maíz y camote.", "Pescado; limón; cebolla roja; ají; cilantro; apio; choclo; camote", ["Pescado", "Apio"], "starter"),
    ("CAMPO-EN-006", "Creme de la crema", "Crema de vegetales de textura sedosa, terminada con queso y pan tostado.", "Zapallo; papa; cebolla; apio; crema de leche; queso; pan de trigo; sal", ["Gluten", "Lácteos", "Apio"], "soup"),
    ("CAMPO-SO-001", "Dieta de pollo", "Caldo de pollo con vegetales y fideos, de sabor suave y reconfortante.", "Pollo; agua; fideos de trigo; zanahoria; papa; apio; hierbas; sal", ["Gluten", "Apio"], "soup"),
    ("CAMPO-SO-002", "Chupe de olluco", "Sopa cremosa de olluco y papa con queso fresco y hierbas.", "Olluco; papa; leche; queso fresco; huevo; cebolla; ajo; huacatay", ["Huevo", "Lácteos"], "soup"),
    ("CAMPO-SO-003", "Chupe de camarón", "Sopa de camarones con arroz, vegetales y una terminación cremosa.", "Camarones; arroz; papa; leche; queso fresco; huevo; cebolla; ají", ["Crustáceos", "Huevo", "Lácteos"], "soup"),
    ("CAMPO-VE-001", "Primavera andina", "Granos y vegetales salteados con una presentación fresca y colorida.", "Quinua; arroz; zanahoria; brócoli; pimiento; salsa de soja; aceite de sésamo", ["Gluten", "Soja", "Sésamo"], "vegetable"),
    ("CAMPO-VE-002", "Kapchi de zetas", "Guiso cremoso de setas y habas con papa y hierbas andinas.", "Setas; habas; papa; leche; queso fresco; cebolla; huacatay; aceite", ["Lácteos"], "vegetable"),
    ("CAMPO-FO-001", "Chicharrón cusqueño", "Cerdo dorado y crujiente acompañado de papa, maíz y salsa criolla.", "Cerdo; papa; maíz; cebolla roja; limón; hierbabuena; ajo; sal", [], "main"),
    ("CAMPO-FO-002", "Trucha y truco", "Trucha dorada con vegetales y una salsa suave de mantequilla y limón.", "Trucha; mantequilla; papa; zanahoria; limón; perejil; sal", ["Pescado", "Lácteos"], "main"),
    ("CAMPO-FO-003", "Uchu de cuy", "Preparación de cuy con salsa de ají y cacahuetes, acompañada de papa.", "Cuy; papa; ají panca; cacahuetes; ajo; cebolla; comino; aceite", ["Cacahuetes"], "main"),
    ("CAMPO-FO-004", "Lomo al vino", "Medallones de res con salsa de vino y champiñones, acompañados de puré.", "Lomo de res; vino tinto; champiñones; mantequilla; leche; papa; cebolla", ["Lácteos", "Sulfitos"], "main"),
    ("CAMPO-FO-005", "Lomo nikei", "Res salteada con vegetales y salsa de inspiración nikkei, acompañada de arroz.", "Lomo de res; arroz; cebolla; pimiento; salsa de soja; jengibre; sésamo; aceite", ["Gluten", "Soja", "Sésamo"], "main"),
    ("CAMPO-FO-006", "Estrogonoff de alpaca", "Tiras de alpaca con champiñones y una salsa cremosa de mostaza.", "Carne de alpaca; champiñones; crema de leche; mostaza; mantequilla; cebolla; arroz", ["Lácteos", "Mostaza"], "main"),
    ("CAMPO-FO-007", "Lomo saltado", "Res salteada a fuego vivo con cebolla y tomate, servida con arroz y papas.", "Lomo de res; cebolla roja; tomate; salsa de soja; papa; arroz; aceite", ["Gluten", "Soja"], "main"),
    ("CAMPO-FO-008", "Desnivel", "Pollo dorado sobre una guarnición de granos y vegetales con salsa cremosa.", "Pollo; quinua; papa; zanahoria; leche; mantequilla; hierbas; aceite", ["Lácteos"], "main"),
    ("CAMPO-FO-009", "Parrilla fusión", "Selección de carnes a la parrilla con papas y una salsa de hierbas.", "Res; pollo; cerdo; papa; mostaza; salsa de soja; ajo; hierbas", ["Gluten", "Soja", "Mostaza"], "main"),
    ("CAMPO-FO-010", "Hamburguesa de res", "Hamburguesa de res con queso, vegetales y salsa de la casa, acompañada de papas.", "Res; pan de trigo con sésamo; queso; lechuga; tomate; mayonesa con huevo; mostaza; papa", ["Gluten", "Huevo", "Lácteos", "Mostaza", "Sésamo"], "main"),
    ("CAMPO-FO-011", "Ensalada andina", "Ensalada de quinua y vegetales con queso, frutos secos y aliño cítrico.", "Quinua; lechuga; tomate; palta; queso fresco; nueces; limón; aceite de oliva", ["Lácteos", "Frutos secos"], "vegetable"),
    ("CAMPO-FO-012", "Pasión andina", "Preparación de granos andinos con vegetales asados y una salsa cremosa.", "Quinua; papa; zapallo; champiñones; crema de leche; queso; hierbas", ["Lácteos"], "main"),
    ("CAMPO-PO-001", "Cheessecake", "Tarta cremosa de queso sobre una base de galleta y cubierta de fruta.", "Queso crema; galletas de trigo; mantequilla; huevo; azúcar; frutos rojos", ["Gluten", "Huevo", "Lácteos"], "dessert"),
    ("CAMPO-PO-002", "Pannacotta de Muña", "Postre de crema de textura delicada, aromatizado con muña.", "Crema de leche; leche; azúcar; gelatina; muña; salsa de fruta", ["Lácteos"], "dessert"),
    ("CAMPO-PO-003", "Banana split", "Banana acompañada de helado, salsa de chocolate y frutos secos.", "Banana; helado de leche y huevo; chocolate; crema batida; nueces; azúcar", ["Huevo", "Lácteos", "Frutos secos"], "dessert"),
    ("CAMPO-PO-004", "Sweet Perú", "Postre de inspiración peruana con crema de lúcuma y una base crujiente.", "Lúcuma; leche; crema de leche; galletas de trigo; huevo; azúcar; pecanas", ["Gluten", "Huevo", "Lácteos", "Frutos secos"], "dessert"),
    ("CAMPO-BC-001", "Americano", "Café negro de sabor equilibrado, preparado con espresso y agua caliente.", "Café; agua", [], "coffee"),
    ("CAMPO-BC-002", "Espresso", "Café corto de aroma intenso y cuerpo concentrado.", "Café; agua", [], "coffee"),
    ("CAMPO-BC-003", "Macchiato", "Espresso con una pequeña cantidad de leche espumada.", "Café; agua; leche", ["Lácteos"], "milk_coffee"),
    ("CAMPO-BC-004", "Capuccino", "Café con leche caliente y una capa de espuma suave.", "Café; agua; leche", ["Lácteos"], "milk_coffee"),
    ("CAMPO-BC-005", "Latte", "Bebida de espresso con abundante leche caliente y espuma ligera.", "Café; agua; leche", ["Lácteos"], "milk_coffee"),
    ("CAMPO-BC-006", "Infusión de manzanilla", "Infusión floral de aroma suave, servida caliente.", "Agua; flores de manzanilla", [], "infusion"),
    ("CAMPO-BC-007", "Infusión de hierba luisa", "Infusión herbal de notas cítricas y aroma fresco.", "Agua; hierba luisa", [], "infusion"),
    ("CAMPO-BC-008", "Infusión de coca", "Infusión caliente de hojas de coca, de sabor herbal.", "Agua; hojas de coca", [], "infusion"),
    ("CAMPO-BC-009", "Infusión de muña", "Infusión de muña de aroma fresco y notas mentoladas.", "Agua; hojas de muña", [], "infusion"),
    ("CAMPO-BC-010", "Té negro", "Té de cuerpo intenso y aroma tostado, servido caliente.", "Agua; hojas de té negro", [], "infusion"),
    ("CAMPO-BC-011", "Infusión de anís", "Infusión de semillas de anís con aroma dulce y especiado.", "Agua; semillas de anís", [], "infusion"),
    ("CAMPO-BC-012", "Aromática de muña, cáscara de naranja y piña", "Infusión frutal y herbal con notas cítricas y un final fresco.", "Agua; muña; cáscara de naranja; piña", [], "infusion"),
    ("CAMPO-BC-013", "Aromática de hierba luisa, kion y limón", "Infusión cítrica con el toque especiado del jengibre.", "Agua; hierba luisa; jengibre; limón", [], "infusion"),
    ("CAMPO-BC-014", "Aromática de cedroncillo, canela y airampo", "Infusión aromática de hierbas y especias con un color intenso.", "Agua; cedroncillo; canela; airampo", [], "infusion"),
    ("CAMPO-BC-015", "Té macho", "Bebida caliente de té, cítricos y especias con un toque de pisco.", "Té negro; agua; pisco; limón; canela; azúcar", [], "cocktail"),
    ("CAMPO-BF-001", "Chicha morada", "Bebida fría de maíz morado y fruta, aromatizada con especias.", "Agua; maíz morado; piña; manzana; canela; clavo de olor; azúcar; limón", [], "juice"),
    ("CAMPO-BF-002", "Limonada", "Bebida de limón recién preparado, servida con hielo.", "Agua; limón; azúcar; hielo", [], "juice"),
    ("CAMPO-BF-003", "Limonada de hierba buena", "Limonada refrescante con aroma de hierbabuena.", "Agua; limón; hierbabuena; azúcar; hielo", [], "juice"),
    ("CAMPO-BF-004", "Muña y piña", "Refresco de piña con una nota herbal de muña.", "Agua; piña; muña; azúcar; hielo", [], "juice"),
    ("CAMPO-BF-005", "Coca Cola", "Gaseosa de cola, servida fría en su presentación comercial.", "Ejemplo de gaseosa de cola: agua carbonatada; azúcar; colorante; acidulante; aromas. Consultar el envase para la composición real", [], "juice"),
    ("CAMPO-BF-006", "Inca Kola", "Gaseosa de sabor dulce y aroma característico, servida fría.", "Ejemplo de gaseosa: agua carbonatada; azúcar; acidulante; aromas; colorante. Consultar el envase para la composición real", [], "juice"),
    ("CAMPO-BF-007", "Agua Munay sin gas", "Agua sin gas, servida fría en su presentación comercial.", "Ejemplo: agua mineral. Consultar el envase para la composición real", [], "water"),
    ("CAMPO-BF-008", "Agua Munay con gas", "Agua con gas de burbuja ligera, servida fría.", "Ejemplo: agua mineral; dióxido de carbono. Consultar el envase para la composición real", [], "water"),
    ("CAMPO-BF-009", "Cusqueña dorada", "Cerveza de estilo dorado con notas de cereal, servida fría.", "Ejemplo de cerveza: agua; malta de cebada; lúpulo; levadura. Consultar el envase para la composición real", ["Gluten"], "beer"),
    ("CAMPO-BF-010", "Cusqueña malta", "Cerveza de perfil maltoso y notas tostadas, servida fría.", "Ejemplo de cerveza: agua; malta de cebada; malta tostada; lúpulo; levadura. Consultar el envase para la composición real", ["Gluten"], "beer"),
    ("CAMPO-BF-011", "Cusqueña trigo", "Cerveza de trigo con aroma de cereal y cuerpo suave.", "Ejemplo de cerveza: agua; malta de trigo; malta de cebada; lúpulo; levadura. Consultar el envase para la composición real", ["Gluten"], "beer"),
    ("CAMPO-BF-012", "Cerveza artesanal", "Cerveza de elaboración artesanal con notas de malta y lúpulo.", "Ejemplo de cerveza: agua; malta de cebada; lúpulo; levadura. Consultar la ficha del fabricante para la composición real", ["Gluten"], "beer"),
    ("CAMPO-PO-005", "Miskilla", "Postre de arroz y chancaca con especias y una terminación cremosa.", "Arroz; chancaca; leche evaporada; leche condensada; canela; clavo de olor; pasas; coco; pecanas", ["Lácteos", "Frutos secos"], "dessert"),
]


def demo_fields(row):
    _, _, description, ingredients, allergens, profile = row
    kcal, carbs, protein, fat, serving = PROFILES[profile]
    return {
        "description": f"{description}\n\n{NOTICE}",
        "ingredients": f"{NOTICE}\n" + "\n-".join(ingredients.split("; ")),
        "nutritional_information": (
            f"{NOTICE}\nPorción de referencia: {serving}.\n"
            f"Energía: {kcal} kcal.\nCarbohidratos: {carbs} g.\n"
            f"Proteínas: {protein} g.\nGrasas: {fat} g.\n"
        ),
        "allergens": "\n".join([
            *allergens,
            ALLERGEN_NOTICE,
            *([] if allergens else ["Sin categorías asignadas en este ejemplo."]),
        ]),
    }
