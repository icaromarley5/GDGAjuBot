#!/usr/bin/env python3
"""Bot do GDG-Aracaju."""
import datetime
import functools
import logging
import random
import re
from collections import OrderedDict

from telegram.ext import CommandHandler, Updater
from telegram.ext.filters import BaseFilter, Filters
from telegram.ext.messagehandler import MessageHandler

from gdgajubot.data.resources import Resources
from gdgajubot.util import do_not_spam
from gdgajubot import util


class FilterSearch(BaseFilter):
    def __init__(self, f):
        self.f = f

    def filter(self, message):
        return Filters.text(message) and self.f(message.text)


# Funções de busca usadas nas easter eggs
find_ruby = re.compile(r"(?i)\bRUBY\b").search
find_java = re.compile(r"(?i)\bJAVA\b").search
find_python = re.compile(r"(?i)\bPYTHON\b").search

# Helpers para definir os handlers do bot
commands = util.HandlerHelper()
easter_egg = util.HandlerHelper()
on_message = util.HandlerHelper()

# Alias para reutilizar o cache como decorator
cache = Resources.cache


# Adapta a assinatura de função esperada por `add_handler` na API nova
def adapt_callback(cb, *args, **kwargs):
    if args:
        cb = functools.partial(cb, *args, **kwargs)
    return lambda _, u, *args, **kwargs: cb(u.message, *args, **kwargs)


ALREADY_ANSWERED_TEXTS = (
    "Ei, olhe, acabei de responder!",
    "Me reservo ao direito de não responder!",
    "Deixe de insistência!",
)

TIME_LEFT = OrderedDict([
    (30, '30 segundos'),
    (60, '1 minuto'),
    (600, '10 minutos'),
    (1800, 'meia hora'),
    (3600, '1 hora'),
])


class GDGAjuBot:
    def __init__(self, config, bot=None, resources=None):
        self.config = config
        self.resources = resources if resources else Resources(config)

        # O parâmetro bot só possui valor nos casos de teste, nesse caso,
        # encerra o __init__ aqui para não haver conexão ao Telegram.
        if bot:
            self.bot = bot
            return

        # Conecta ao telegram com o token passado na configuração
        self.updater = Updater(token=config.telegram_token)
        self.bot = self.updater.bot

        # Anexa uma função da API antiga para manter retrocompatibilidade
        self.bot.reply_to = lambda message, text, **kwargs: \
            self.bot.send_message(
                chat_id=message.chat_id, text=text,
                reply_to_message_id=message.message_id, **kwargs
            )

        # Configura os comandos aceitos pelo bot
        dispatcher = self.updater.dispatcher
        for k, function in commands.functions:
            name = k[1:] if k[0] == '/' else k
            dispatcher.add_handler(
                CommandHandler(name, adapt_callback(function, self)))

        # Configura os comandos personalizados
        if self.config.custom_responses:
            for command, response in self.config.custom_responses.items():
                name = command.replace('/', '')
                custom = functools.partial(
                    adapt_callback(self.custom_response_template),
                    command=name, response_text=response
                )
                dispatcher.add_handler(
                    CommandHandler(name, custom)
                )

        # Configura as easter eggs
        for search, function in easter_egg.functions:
            dispatcher.add_handler(
                MessageHandler(FilterSearch(search), adapt_callback(do_not_spam(function), self)))

        # Configura as funções que reagem a todas as mensagens de texto
        if on_message.functions:
            def adapt_search(xs):
                pattern, function = xs
                return re.compile(pattern).search, function

            def sub_dispatcher(_, update, *, actions=list(map(adapt_search, on_message.functions))):
                for search, function in actions:
                    if search(update.message.text):
                        function(self, update.message)

            dispatcher.add_handler(
                MessageHandler(
                    filters=Filters.text,
                    callback=sub_dispatcher,
                ),
                group=1,
            )

    def custom_response_template(
        self, message, *args, command='', response_text=''
    ):
        logging.info(command)
        self.bot.reply_to(message, response_text)

    @commands('/start')
    def send_welcome(self, message):
        """Mensagem de apresentação do bot."""
        logging.info("/start")
        start_message = "Olá! Eu sou o bot para %s! Se precisar de ajuda: /help" % (
            ', '.join(self.config.group_name))
        self.bot.reply_to(message, start_message)

    @commands('/help')
    def help(self, message):
        """Mensagem de ajuda do bot."""
        logging.info("/help")
        help_message = "/help - Exibe essa mensagem.\n" \
            "/about - Sobre o bot e como contribuir.\n" \
            "/book - Informa o ebook gratuito do dia na Packt Publishing.\n"
        if len(self.config.group_name) > 1:
            help_message += "/events - Informa a lista de próximos eventos dos grupos: {group_name}."
        else:
            help_message += "/events - Informa a lista de próximos eventos do {group_name}."

        self.bot.reply_to(
            message,
            help_message.format(
                group_name=', '.join(self.config.group_name))
        )

    @commands('/links')
    def links(self, message):
        """Envia uma lista de links do grupo associado."""
        logging.info("/links")
        social_links = self.config.links
        if social_links:
            response = '*Esses são os links para o nosso grupo:*\n\n'
            for link_type, link_url in social_links.items():
                response += "🔗 {type}: {url}\n".format(
                    type=link_type.capitalize(),
                    url=link_url
                )
        else:
            response = 'Não existem links associados a esse grupo.'
        self._send_smart_reply(
            message, response,
            parse_mode="Markdown", disable_web_page_preview=True)

    @commands('/events')
    def list_upcoming_events(self, message):
        """Retorna a lista de eventos do Meetup."""
        logging.info("%s: %s", message.from_user.name, "/events")
        try:
            next_events = self.resources.get_events(5)
            if next_events:
                response = self._format_events(next_events)
            else:
                response = "Não há nenhum futuro evento do grupo {0}.".format(
                    self.config.group_name)
            self._send_smart_reply(
                message, response,
                parse_mode="Markdown", disable_web_page_preview=True
            )
        except Exception as e:
            logging.exception(e)

    def _format_events(self, events):
        response = []
        for event in events:
            # If the events wasn't in cache, event['time'] is a datetime object
            # So we format it!
            if isinstance(event['time'], datetime.datetime):
                # create a pretty-looking date
                formatting = '%d/%m %Hh'
                if event['time'].minute:
                    formatting += '%M'
                event['time'] = event['time'].strftime(formatting)

            response.append("[%(name)s](%(link)s): %(time)s" % event)
        return '\n'.join(response)

    @on_message('.*')
    def extract_and_save_data(self, message, *args, **kwargs):
        self.resources.log_message(message, *args, **kwargs)

    @on_message('.*')
    def ensure_daily_book(self, message):
        # using cache to avoid too much processing
        ensure_cache = Resources.cache.get_cache('ensure_daily_book')
        count = ensure_cache.get(message.chat_id, createfunc=int) + 1
        ensure_cache[message.chat_id] = count

        # consider to send if passed at least 50 messages
        if count >= 50:
            logging.info("ensure_daily_book: checagens para enviar o livro do dia")

            # we send only if /book was called at least 6 hours ago or one hour ago if in the end of the day
            last = self.resources.last_book_sent(message.chat_id)
            if last:
                now = datetime.datetime.now(tz=util.UTC_TZ)
                duration = (now - last).total_seconds()
                if duration >= 21600 or duration >= 3600 and now.hour == 22:
                    self.packtpub_free_learning(message, reply=False)
                    logging.info("ensure_daily_book: livro do dia enviado")

    @commands('/book')
    def packtpub_free_learning(self, message, now=None, reply=True):
        """Retorna o livro disponível no free-learning da editora PacktPub."""
        if reply:
            logging.info("%s: %s", message.from_user.name, "/book")
            send_message = self._send_smart_reply
        else:
            send_message = self.send_text_photo

        book, response, left = self.__get_book(now)
        if left is not None:
            warning = "⌛️ Menos de %s!" % TIME_LEFT[left]
            response += warning

        cover = book['cover'] if book else None

        has_sent = send_message(
            message, response,
            parse_mode="Markdown", disable_web_page_preview=True,
            picture=cover
        )

        if has_sent:
            ensure_cache = Resources.cache.get_cache('ensure_daily_book')
            ensure_cache[message.chat_id] = 0
            self.resources.last_book_sent(message.chat_id, message.chat.username, update=True)

    def __get_book(self, now=None):
        # Faz duas tentativas para obter o livro do dia, por questões de possível cache antigo.
        for _ in range(2):
            book = self.resources.get_packt_free_book()
            if book is None:
                continue

            if now is None:
                now = datetime.datetime.now(tz=util.AJU_TZ)

            delta = datetime.datetime.fromtimestamp(book.expires, tz=util.AJU_TZ) - now
            delta = delta.total_seconds()
            if delta < 0:
                continue

            response = (
                "Confira o livro gratuito de hoje da Packt Publishing 🎁\n\n"
                "📖 [%s](%s)\n"
                "🔎 %s\n"
            ) % (book.name, Resources.BOOK_URL, book.summary)

            for left in TIME_LEFT:
                if delta <= left:
                    return book, response, left
            else:
                left = None

            break

        # As tentativas falharam...
        else:
            Resources.cache.invalidate(Resources.get_packt_free_book, "get_packt_free_book")
            book = None
            response = "Parece que não tem um livro grátis hoje 😡\n\n" \
                       "Se acha que é um erro meu, veja com seus próprios olhos em " + Resources.BOOK_URL
            left = None

        return book, response, left

    def send_text_photo(self, message, text, picture=None, reply_to=False, **kwargs):
        if reply_to:
            kwargs['reply_to_message_id'] = message.message_id

        if picture:
            self.bot.send_photo(message.chat_id, photo=picture, **kwargs)
            if reply_to:
                del kwargs['reply_to_message_id']

        return self.bot.send_message(message.chat_id, text, **kwargs)

    def _send_smart_reply(self, message, text, picture=None, **kwargs):
        send_message = functools.partial(self.send_text_photo, message, text, picture,
                                         reply_to=True, **kwargs)

        # On groups or supergroups, check if I have
        # a recent previous response to refer
        if message.chat.type in ["group", "supergroup"]:
            # Retrieve from cache and set if necessary
            key = "p%s" % util.extract_command(text)
            previous_cache = Resources.cache.get_cache(key, expire=600)
            previous = previous_cache.get(key=message.chat.id, createfunc=dict)

            # Verify if previous response is the same
            # to send a contextual response
            if previous.get('text') == text:
                self.bot.send_message(
                    message.chat.id, '👆 ' + random.choice(ALREADY_ANSWERED_TEXTS),
                    reply_to_message_id=previous['message_id']
                )
                return False

            # or, send new response and update the cache
            else:
                sent = send_message()
                previous.update({'text': text, 'message_id': sent.message_id})
                previous_cache[message.chat.id] = previous  # reset expire time

        # On private chats or channels, send the normal reply...
        else:
            send_message()

        return True

    @commands('/about')
    def about(self, message):
        logging.info("%s: %s", message.from_user.name, "/about")
        response = "Esse bot obtém informações de eventos do Meetup ou Facebook. "
        response += "Para saber mais ou contribuir: https://github.com/GDGAracaju/GDGAjuBot/"
        self.bot.send_message(message.chat.id, response)

    @commands('/list_users')
    def list_users(self, message):
        if self.resources.is_user_admin(message.from_user.id):
            users = self.resources.list_all_users()
            response = '\n'.join([str(user) for user in users])
            self.bot.send_message(message.chat.id, response)

    @easter_egg(find_ruby)
    def love_ruby(self, message):
        """Easter Egg com o Ruby."""
        logging.info("%s: %s", message.from_user.name, "ruby")
        username = message.from_user.name
        self.bot.send_message(
            message.chat.id,
            "{} ama Ruby... ou Rails?".format(username),
        )

    @easter_egg(find_java)
    def memory_java(self, message):
        """Easter Egg com o Java."""
        logging.info("%s: %s", message.from_user.name, "java")
        self.bot.send_message(message.chat.id, "Ihh... acabou a RAM")

    @easter_egg(find_python)
    def easter_python(self, message):
        """Easter Egg com o Python."""
        logging.info("%s: %s", message.from_user.name, "python")
        self.bot.send_message(message.chat.id, "import antigravity")

    def start(self):
        self.updater.start_polling(clean=True)
        logging.info("GDGAjuBot iniciado")
        logging.info("Este é o bot do {0}".format(self.config.group_name))
        if self.config.debug_mode:
            logging.info("Modo do desenvolvedor ativado")
            logging.info("Usando o bot %s", self.bot.get_me().name)
            logging.info(
                "Usando telegram_token={0}".format(self.config.telegram_token))
            logging.info(
                "Usando meetup_key={0}".format(self.config.meetup_key))
