import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import urljoin

WEB_URL = "https://www.arimainmo.com/es/inversores/notas-de-prensa"
BASE_URL = "https://www.arimainmo.com"
OUTPUT_FILE = Path("arima.xml")


def descargar_notas():
    solicitud = urllib.request.Request(
        WEB_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            )
        },
    )

    with urllib.request.urlopen(solicitud, timeout=60) as respuesta:
        contenido = respuesta.read()

    soup = BeautifulSoup(contenido, "html.parser")
    notas = []
    enlaces_encontrados = set()

    for elemento in soup.select("a.item-download"):
        enlace = elemento.get("data-href") or elemento.get("href")

        titulo_elemento = elemento.select_one("p")
        fecha_elemento = elemento.select_one("span")

        if not enlace or not titulo_elemento:
            continue

        enlace = urljoin(BASE_URL, enlace)
        titulo = titulo_elemento.get_text(" ", strip=True)

        fecha = ""

        if fecha_elemento:
            fecha = fecha_elemento.get_text(" ", strip=True)

        if not titulo or enlace in enlaces_encontrados:
            continue

        enlaces_encontrados.add(enlace)

        notas.append(
            {
                "titulo": titulo,
                "enlace": enlace,
                "fecha": fecha,
            }
        )

    return notas


def crear_rss(notas):
    rss = ET.Element(
        "rss",
        {
            "version": "2.0",
            "xmlns:atom": "http://www.w3.org/2005/Atom",
        },
    )

    canal = ET.SubElement(rss, "channel")

    ET.SubElement(canal, "title").text = "Notas de prensa de Árima"
    ET.SubElement(canal, "link").text = WEB_URL
    ET.SubElement(canal, "description").text = (
        "Últimas notas de prensa publicadas por "
        "Árima Real Estate SOCIMI"
    )
    ET.SubElement(canal, "language").text = "es"
    ET.SubElement(canal, "lastBuildDate").text = format_datetime(
        datetime.now(timezone.utc)
    )

    enlace_atom = ET.SubElement(
        canal,
        "{http://www.w3.org/2005/Atom}link",
    )
    enlace_atom.set("href", WEB_URL)
    enlace_atom.set("rel", "self")
    enlace_atom.set("type", "application/rss+xml")

    for nota in notas:
        elemento = ET.SubElement(canal, "item")

        ET.SubElement(elemento, "title").text = nota["titulo"]
        ET.SubElement(elemento, "link").text = nota["enlace"]

        ET.SubElement(elemento, "description").text = (
            f"{nota['titulo']}. Documento publicado por "
            "Árima Real Estate SOCIMI."
        )

        ET.SubElement(elemento, "category").text = "Notas de prensa"

        identificador = ET.SubElement(elemento, "guid")
        identificador.set("isPermaLink", "true")
        identificador.text = nota["enlace"]

        if nota["enlace"].lower().endswith(".pdf"):
            adjunto = ET.SubElement(elemento, "enclosure")
            adjunto.set("url", nota["enlace"])
            adjunto.set("type", "application/pdf")
            adjunto.set("length", "0")

        if nota["fecha"]:
            try:
                fecha_publicacion = datetime.strptime(
                    nota["fecha"],
                    "%d/%m/%Y",
                ).replace(tzinfo=timezone.utc)

                ET.SubElement(elemento, "pubDate").text = format_datetime(
                    fecha_publicacion
                )
            except ValueError:
                pass

    ET.indent(rss, space="  ")

    arbol = ET.ElementTree(rss)
    arbol.write(
        OUTPUT_FILE,
        encoding="utf-8",
        xml_declaration=True,
    )


def main():
    notas = descargar_notas()

    if not notas:
        raise RuntimeError(
            "No se encontraron notas de prensa de Árima"
        )

    crear_rss(notas)

    print(f"RSS creada correctamente con {len(notas)} notas")


if __name__ == "__main__":
    main()
