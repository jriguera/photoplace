#!/bin/sh
# esto es un comentario

exiftool > /dev/null 2>&1
if [ $? != 0 ]; then 
    echo "No existe exiftool en este equipo ... Instalandolo"
    tar -zxvf exiftool-linux.tgz > instalacion_exiftool.log
    export PATH=$PATH:./Image-ExifTool-8.16
fi

echo "Programa para geolocalizar fotos y generar kmz en dos pasos."

DIRIN=FOTOS
GPXIN=ruta.gpx
OUTPUT=ruta.kmz

if [ ! -d "$DIRIN" ]; then
    echo "El directorio de fotos $DIRIN no existe!"
fi

if [ ! -e "$GPXIN" ]; then
    echo "El fichero GPX $GPXIN no existe!"
fi

echo "Lanzando programa para geolocalizar fotos en el directorio ..."
exiftool -config ExifTool.cfg -v2 -geotag "$GPXIN" "$DIRIN" > "$DIRIN"/geolocation.log 2>&1
echo "Borrando fotos de backup ..."
for file in "$DIRIN"/*_original; do
    rm -f "$file" 
done

echo "Lanzando programa para generar KMZ ..."
python photoplace.py -n -i "$DIRIN" -o "$OUTPUT"

exit 1
