CLS
@ECHO OFF
REM Esto e un comentario
ECHO.
ECHO. Programa para geolocalizar fotos y generar kmz en dos pasos.
ECHO.
REM directorio onde vai analizar as fotos
SET DIRIN=FOTOS
SET GPXIN=ruta.gpx
SET OUTPUT=ruta.kmz
REM SET DIRIN=%USERPROFILE%\Desktop\%DIRIN%
REM SET GPXIN=%USERPROFILE%\Desktop\%GPXIN%
REM SET OUTPUT=%USERPROFILE%\Desktop\%OUTPUT%
IF NOT EXIST %DIRIN% GOTO END1
IF NOT EXIST %GPXIN% GOTO END1
ECHO Lanzando programa para geolocalizar fotos en el directorio ...
exiftool.exe -config ExifTool.cfg -v2 -geotag %GPXIN% %DIRIN% > %DIRIN%/geolocation.log 2>&1
ECHO Borrando fotos  de backup ...
FOR %%x in (%DIRIN%\*.*_original) DO del /F /Q %%x

ECHO Lanzando programa para generar KMZ ...
python photoplace.py -n -i %DIRIN% -o %OUTPUT%

ECHO Lanzando google Earth ...
IF EXIST %OUTPUT% GOTO END

GOTO END

:END1
ECHO El directorio de fotos %DIRIN% no existe!
PAUSE

:END2
ECHO El fichero GPX %GPXIN% no existe!
PAUSE

:END
REM Copiando kmz al escritorio
REM copy /B /Y %OUTPUT% "%USERPROFILE%\Escritorio"
REM copy /B /Y %OUTPUT% "%USERPROFILE%\Desktop"
REM Lanzando google earth
call "%OUTPUT%"

