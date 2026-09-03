# 🔥 GangaCheck.es — Detector y Tasador de Chollos de Segunda Mano

MVP funcional para **gangacheck.es**: una plataforma web que analiza enlaces de anuncios de segunda mano (empezando por Wallapop), calcula la mediana de mercado, evalúa la fiabilidad del vendedor y genera una puntuación visual del **0 al 10** (*Chollo Score*).

---

## 🚀 Cómo ejecutar en tu ordenador (Coste 0 €)

### 1. Instalar dependencias
Abre una terminal PowerShell en la carpeta del proyecto:

```powershell
pip install -r backend/requirements.txt
```

### 2. Iniciar el servidor
```powershell
python backend/app.py
```

### 3. Abrir en el navegador
Entra en:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🎯 Cómo probarlo

Puedes probar con cualquier enlace real de Wallapop o hacer clic en los ejemplos rápidos de la web:
- **PS5 Chollo (270 €):** Obtendrá una puntuación alta (~8.8/10) destacando el ahorro frente a la mediana de 380 €.
- **iPhone 15 Estafa (250 €):** El algoritmo activará el kill-switch anti-estafa (descuento anormal, cuenta sin reviews, pago por Bizum) y bajará la nota a 1.2/10 con alerta roja.
- **Switch Precio Alto (290 €):** Mostrará advertencia de sobreprecio y sugerencia de alternativa garantizada.

---

## 🌐 Cómo conectar tu dominio `gangacheck.es` gratis

1. **Subir el código a GitHub:**
   - Crea un repositorio privado o público en GitHub y sube esta carpeta.
2. **Desplegar gratis en Vercel o Render:**
   - Conecta tu repositorio de GitHub a [Vercel](https://vercel.com) o [Render](https://render.com).
3. **Configurar DNS en Nominalia / Cloudflare:**
   - Añade un registro CNAME que apunte `gangacheck.es` a tu despliegue de Vercel/Render.
   - ¡Listo! Tu web tendrá certificado SSL (`https://gangacheck.es`) automático y gratuito.
