import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

class ListaSuperBot:
    def __init__(self):
        self.archivo_lista_grupal = 'lista_grupo.json'
        self.archivo_listas_individuales = 'listas_individuales.json'
        
        # Cargar listas desde archivos
        self.lista_grupal = self.cargar_archivo(self.archivo_lista_grupal, [])
        self.listas_individuales = self.cargar_archivo(self.archivo_listas_individuales, {})

    def cargar_archivo(self, ruta, default):
        """Carga un archivo JSON. Si no existe, devuelve un valor por defecto."""
        try:
            with open(ruta, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    def guardar_archivo(self, ruta, data):
        """Guarda datos en un archivo JSON."""
        with open(ruta, 'w') as f:
            json.dump(data, f)

    def obtener_lista(self, chat_id, es_grupo):
        """Obtiene la lista adecuada, ya sea grupal o individual."""
        return self.lista_grupal if es_grupo else self.listas_individuales.get(str(chat_id), [])

    def guardar_lista(self, chat_id, lista, es_grupo):
        """Guarda la lista adecuada, ya sea grupal o individual."""
        if es_grupo:
            self.lista_grupal = lista
            self.guardar_archivo(self.archivo_lista_grupal, self.lista_grupal)
        else:
            self.listas_individuales[str(chat_id)] = lista
            self.guardar_archivo(self.archivo_listas_individuales, self.listas_individuales)

    async def agregar_producto(self, update: Update, context):
        """Agrega un producto a la lista."""
        await self.manejar_producto(update, context, agregar=True)

    async def eliminar_producto(self, update: Update, context):
        """Elimina un producto de la lista."""
        await self.manejar_producto(update, context, agregar=False)

    async def manejar_producto(self, update: Update, context, agregar=True):
        """Maneja tanto la adición como la eliminación de productos."""
        chat_id = update.effective_chat.id
        es_grupo = update.effective_chat.type in ['group', 'supergroup']
        
        producto = ' '.join(context.args)
        lista = self.obtener_lista(chat_id, es_grupo)

        if agregar:
            if producto:
                lista.append(producto)
                mensaje = f'Producto "{producto}" agregado a la lista.'
            else:
                mensaje = 'Por favor, proporciona el nombre del producto que deseas agregar.'
        else:
            if producto in lista:
                lista.remove(producto)
                mensaje = f'Producto "{producto}" eliminado de la lista.'
            else:
                mensaje = f'El producto "{producto}" no está en la lista.'

        self.guardar_lista(chat_id, lista, es_grupo)
        await update.message.reply_text(mensaje)

    async def mostrar_lista(self, update: Update, context):
        """Muestra la lista completa."""
        chat_id = update.effective_chat.id
        es_grupo = update.effective_chat.type in ['group', 'supergroup']
        
        lista = self.obtener_lista(chat_id, es_grupo)
        mensaje = '\n'.join(lista) if lista else 'La lista está vacía.'
        await update.message.reply_text(f'Lista de supermercado:\n{mensaje}')

    async def eliminar_lista(self, update: Update, context):
        """Elimina toda la lista."""
        chat_id = update.effective_chat.id
        es_grupo = update.effective_chat.type in ['group', 'supergroup']
        
        self.guardar_lista(chat_id, [], es_grupo)
        await update.message.reply_text('¡La lista ha sido eliminada por completo!')

    async def manejar_mensaje_texto(self, update: Update, context):
        """Agrega un producto a la lista directamente desde un mensaje."""
        chat_id = update.effective_chat.id
        es_grupo = update.effective_chat.type in ['group', 'supergroup']
        
        producto = update.message.text
        lista = self.obtener_lista(chat_id, es_grupo)
        lista.append(producto)
        
        self.guardar_lista(chat_id, lista, es_grupo)
        await update.message.reply_text(f'Producto "{producto}" agregado a la lista.')

    async def start(self, update: Update, context):
        """Muestra un mensaje de bienvenida cuando se inicia el bot."""
        mensaje = (
            "¡Hola! Soy tu bot de lista de supermercado.\n"
            "Usa /info para ver los comandos disponibles."
        )
        await update.message.reply_text(mensaje)

    async def info(self, update: Update, context):
        """Muestra la lista de comandos disponibles."""
        mensaje = (
            "Estos son los comandos disponibles:\n"
            "/agregar [producto] - Agrega un producto a la lista\n"
            "/eliminar [producto] - Elimina un producto de la lista\n"
            "/lista - Muestra la lista completa\n"
            "/eliminar_lista - Elimina toda la lista\n"
            "/start - Inicia el bot\n"
            "/info - Muestra la lista de comandos"
        )
        await update.message.reply_text(mensaje)

    def cargar_token(self, archivo_config):
        """Carga el token desde un archivo JSON."""
        with open(archivo_config, 'r') as f:
            config = json.load(f)
        return config.get('TOKEN')

    def iniciar_bot(self, archivo_config):
        """Configura y ejecuta el bot."""
        token = self.cargar_token(archivo_config)
        if not token:
            raise ValueError("Token no encontrado en el archivo de configuración.")

        application = Application.builder().token(token).build()

        # Manejar comandos
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("info", self.info))
        application.add_handler(CommandHandler("agregar", self.agregar_producto))
        application.add_handler(CommandHandler("eliminar", self.eliminar_producto))
        application.add_handler(CommandHandler("lista", self.mostrar_lista))
        application.add_handler(CommandHandler("eliminar_lista", self.eliminar_lista))

        # Manejar mensajes de texto sin comando
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.manejar_mensaje_texto))

        # Iniciar el bot
        application.run_polling()

if __name__ == '__main__':
    bot = ListaSuperBot()
    CONFIG_FILE = 'config.json'
    bot.iniciar_bot(CONFIG_FILE)
