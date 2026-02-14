@echo off
rgbasm badapple.s -o badapple.o
rgblink badapple.o -o badapple.gb -n badapple.sym -m badapple.map
py "D:\Code\gbstuff\gbromheader.py" -t BadApple -o badapple.gb -e export -m mbc3 -r 128 -s 0
echo Compiled!
