# coding: utf-8
import requests
from django.conf import settings


def send_message(to, msg):
    """
    Permet d'envoyer un message à une liste de numéros de téléphones
    :param to: Numéro(s) de téléphone
    :param msg: Message à envoyer
    :return: Vrai si le message a été envoyé, faux sinon
    """
    if isinstance(to, str):
        to = [to]
    if not to:
        return False
    return requests.post(settings.SMS_GATEWAY_URL, json=dict(
        email=settings.SMS_GATEWAY_LOGIN,
        password=settings.SMS_GATEWAY_PASSWORD,
        device=settings.SMS_GATEWAY_DEVICE,
        number=to,
        message=msg,
    )).status_code == 200
