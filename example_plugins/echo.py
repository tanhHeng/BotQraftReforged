"""Reply passively with the text and images supplied to /echo."""
from types import ModuleType
from botqraft.api.command import GreedyText, QQCommandSource, SimpleCommandBuilder
from botqraft.api.qtext import QImage
from botqraft.api.types import QQPluginServerInterface


PLUGIN_METADATA = {
    'id': 'echo',
    'version': '1.1.0',
    'name': 'Echo',
    'description': 'Passively echo the supplied text and images',
    'dependencies': {'botqraft': '>=0.1.0'},
}

# Marks where an image was in the echoed text; the image itself follows as its own message.
IMAGE_PLACEHOLDER = '[image]'


def images_of(source: QQCommandSource) -> list[QImage]:
    images = []
    for attachment in source.message_data.attachments or []:
        content_type = str(attachment.content_type or '')
        url = attachment.url
        # QQ gives each received image a download URL; the platform fetches it again for the reply.
        if content_type.startswith('image/') and isinstance(url, str) and url.startswith(('http://', 'https://')):
            images.append(QImage(url))
    return images


def echo(server: QQPluginServerInterface, source: QQCommandSource, text: str = '') -> None:
    images = images_of(source)
    if not text and not images:
        source.reply(server.rtr('echo.usage'))
        return
    if text:
        # Media messages cannot carry text, so text goes first with one placeholder per image.
        source.reply(text + f' {IMAGE_PLACEHOLDER}' * len(images))
    # Each image is a separate passive reply; the original source supplies the reply association.
    for image in images:
        source.reply(image)


def on_load(server: QQPluginServerInterface, prev_module: ModuleType | None) -> None:
    server.register_translation('en_us', {'echo': {'usage': 'Usage: /echo <text>, optionally with images'}})
    server.register_translation('zh_cn', {'echo': {'usage': '用法：/echo <文本>，也可以附带图片'}})
    # Declare the command path separately from its argument node type.
    builder = SimpleCommandBuilder()
    # An image-only message arrives as plain "/echo", so the bare root also runs.
    builder.command('/echo', lambda source: echo(server, source))
    builder.command('/echo <text>', lambda source, context: echo(server, source, context['text']))
    # GreedyText preserves spaces in the supplied reply text.
    builder.arg('text', GreedyText)
    builder.register(server)
    # Help resolves this language dictionary for the viewer or panel language.
    server.register_help_message('/echo', {
        'zh_cn': '复述提供的文本和图片',
        'en_us': 'Echo the supplied text and images',
    })
