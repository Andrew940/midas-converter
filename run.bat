@echo off
REM setup vars of open vino
CALL "C:\Program Files (x86)\IntelSWTools\openvino\bin\setupvars.bat"

python monodepth_demo.py -m public\midasnet\FP32\midasnet.xml -i images/office.jpg