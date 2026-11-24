import os
from secrets import token_urlsafe

from flask import g, request, session
from werkzeug.middleware.proxy_fix import ProxyFix


def nonce_csp():
    if "nonce_csp" not in g:
        g.nonce_csp = token_urlsafe(24)
    return g.nonce_csp


def configurar_protecao_http(app):
    # Habilite somente atrás de um proxy confiável que defina X-Forwarded-Proto.
    if os.getenv("STUDYHUB_PROXY_HTTPS") == "1":
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=0, x_proto=1)

    app.jinja_env.globals["nonce_csp"] = nonce_csp

    @app.after_request
    def proteger_resposta(resposta):
        resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
        resposta.headers.setdefault("X-Frame-Options", "DENY")
        resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if request.is_secure:
            resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        if resposta.mimetype == "text/html":
            resposta.headers.setdefault("Content-Security-Policy", (
                "default-src 'self'; "
                "base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; "
                f"script-src 'self' 'nonce-{nonce_csp()}' https://cdn.jsdelivr.net "
                "https://www.googletagmanager.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://res.cloudinary.com https://*.google-analytics.com https://www.googletagmanager.com; "
                "connect-src 'self' https://*.google-analytics.com https://*.analytics.google.com "
                "https://www.googletagmanager.com"
            ))
        if request.endpoint != "static" and (
            session.get("usuario_id") or request.cookies.get(app.config["SESSION_COOKIE_NAME"])
        ):
            resposta.cache_control.no_store = True
            resposta.cache_control.private = True
        return resposta
