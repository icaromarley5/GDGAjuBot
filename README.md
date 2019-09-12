# GDG Aracaju Bot

[![Build Status](https://travis-ci.org/GDGAracaju/GDGAjuBot.svg?branch=master)](https://travis-ci.org/GDGAracaju/GDGAjuBot)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

O GDG Aracaju Bot, ou `gdgajubot` é um bot de [Telegram](https://telegram.me/) com a função
principal de informar eventos no [Meetup](http://www.meetup.com/), além de outras.

## Funcionalidades

O bot atende aos seguintes comandos:

- `/start`: Mensagem de apresentação do bot.
- `/help`: Mensagem de ajuda do bot.
- `/links`: Envia uma lista de links do grupo associado.
- `/dump_states`: (admin).
- `/about`: Exibe informações sobre o bot.
- `/events`: listagem dos próximos eventos registrados no meetup.
- `/book`: livro gratuito do dia da editora [Packt Publishing](https://www.packtpub.com/).
- `/udemy`: lista de cursos com cupons limitados de 100% de desconto do site [Udemy](https://www.udemy.com/).
- `/list_users`: (admin) Lista todos os usuários.

As seguintes funções estão disponíveis em `beta`:

- `/auto_events`: notifica automaticamente o usuário quando houver novos eventos.
- `/auto_book`: notifica automaticamente o usuário quando houver um novo livro gratuito.

Há também alguns recursos escondidos: olhem os fontes!

## Instalação

A instalação é simples, basta baixar o projeto, descompactar e executar:

    $ python setup.py install

Ou, se estiver usando `pip`, basta executar diretamente:

    $ pip install git+https://github.com/GDGAracaju/GDGAjuBot.git

Em qualquer um dos métodos, o script `gdgajubot` será instalado. Verifique se ele está disponível
chamando pela linha de comando:

    $ gdgajubot --help

### Dependências

O `gdgajubot` precisa no mínimo do Python 3.6.

No momento da instalação, as dependências mínimas listadas no arquivo `setup.py` serão baixadas
automaticamente. Para desenvolver o `gdgajubot`, recomendamos a instalação das dependências listadas
no arquivo `Pipfile` via:

    $ pipenv install

Para isso, é necessário ter o `pipenv` instalado.

## Modo de uso

### Pré-requisitos

Antes de começar, é necessário um token do Telegram [obtido com o @BotFather](https://core.telegram.org/bots#6-botfather),
que vincula ao seu bot, e o id do cliente, segredo do cliente e refresh token [obtidos ao seguir o passo 1 e 2 descrito em](https://www.meetup.com/pt-BR/meetup_api/auth/#oauth2),
para ter permissões de acesso à API do Meetup.

### Iniciar o bot

Para o bot ser iniciado, execute

    $ gdgajubot -t 'TELEGRAM_TOKEN' -mcid 'MEETUP_CLIENT_ID' -mcs 'MEETUP_CLIENT_SECRET' -mrt 'MEETUP_REFRESH_TOKEN' -g 'GROUP_NAME'

onde `TELEGRAM_TOKEN` é o token do seu bot, `MEETUP_CLIENT_ID` o id do cliente do Meetup, `MEETUP_CLIENT_SECRET` o segredo do cliente do Meetup, `MEETUP_REFRESH_TOKEN` o refresh token do Meetup e `GROUP_NAME` o nome do
grupo do Meetup onde o bot irá buscar os eventos.

No Windows, use:

    $ python scripts\gdgajubot

O bot também pode ser executado definindo variáveis de ambiente

    $ export TELEGRAM_TOKEN='token do bot'
    $ export MEETUP_CLIENT_ID='id do cliente do meetup'
    $ export MEETUP_CLIENT_SECRET='segredo do cliente do meetup'
    $ export MEETUP_REFRESH_TOKEN='refresh token do meetup'
    $ export GROUP_NAME='grupo do meetup'
    $ gdgajubot

Usando as variáveis de ambiente, é possível pôr as credenciais em um arquivo separado e importar
para o shell antes de executar:

    $ . credenciais_bot
    $ gdgajubot -g 'GROUP_NAME'

Existe um parâmetro opcional que permite encurtar as URLs fornecidas pelo bot: `--url_shortener_key` (ou variável de ambiente `URL_SHORTENER_KEY`). [Para obter essa chave, visite a documentação](https://developers.google.com/url-shortener/v1/getting_started).

### Testando

O `gdgajubot` é desenvolvido com testes automatizados, porém usando dados estáticos. Para verificar
se o seu bot está funcionando de verdade, inicie uma conversa com ele com um cliente Telegram.
Escreva `/events`,`/book` ou `/udemy` e veja se ele responde.
