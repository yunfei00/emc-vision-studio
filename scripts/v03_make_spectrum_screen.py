"""Create a fictional, stable spectrum-analyzer screen for cinematic compositing.

This is illustrative data, NOT a real RF measurement.
Uses Pillow only; generated PNG is not committed to GitHub.
"""
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math

def font(size):
    paths = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="D:/AI-Video/private/lost-signal/v0.3/spectrum_screen.png")
    args = p.parse_args()
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), (7, 19, 31))
    d = ImageDraw.Draw(im)
    cyan, green, yellow, muted = (78, 221, 232), (105, 239, 153), (250, 210, 85), (144, 171, 186)
    d.rectangle((10, 10, W-11, H-11), outline=(42, 93, 113), width=3)
    d.rectangle((20, 20, W-21, 93), fill=(15, 40, 56))
    d.text((40, 29), "SPECTRUM ANALYZER  /  SIMULATION", font=font(29), fill=cyan)
    d.text((40, 65), "SCENE PROP  -  NOT A REAL MEASUREMENT", font=font(18), fill=muted)
    d.text((845, 35), "CENTER  2.450000 GHz", font=font(25), fill=(230, 241, 245))
    x0, y0, x1, y1 = 105, 135, 1200, 595
    d.rectangle((x0, y0, x1, y1), outline=(59, 118, 135), width=2)
    for i in range(11):
        x = x0 + (x1-x0)*i//10
        d.line((x,y0,x,y1), fill=(27, 66, 81), width=2)
    for i in range(9):
        y = y0 + (y1-y0)*i//8
        d.line((x0,y,x1,y), fill=(27, 66, 81), width=2)
        d.text((18,y-14), f"{-30-i*10:>4} dBm", font=font(19), fill=muted)
    points=[]
    for i in range(x1-x0+1):
        x=x0+i
        peak=270*math.exp(-((i-560)/32)**2)
        side=95*math.exp(-((i-720)/65)**2)
        noise=12*math.sin(i*.075)+8*math.sin(i*.27)+5*math.sin(i*.63)
        y=int(max(y0+12,min(y1-12,y1-67-peak-side-noise)))
        points.append((x,y))
    d.line(points, fill=green, width=3, joint="curve")
    marker_x=x0+560
    marker_y=points[560][1]
    d.line((marker_x,y0,marker_x,y1), fill=(150, 126, 48), width=2)
    d.ellipse((marker_x-7,marker_y-7,marker_x+7,marker_y+7), fill=yellow)
    d.rectangle((x0+15,y0+15,x0+490,y0+88), fill=(13, 36, 49))
    d.text((x0+28,y0+22), "M1  2.450000 GHz", font=font(27), fill=yellow)
    d.text((x0+28,y0+56), "PEAK  -48.6 dBm  (SIMULATED)", font=font(20), fill=(235, 238, 226))
    d.text((x0, 614), "START  2.400 GHz", font=font(23), fill=cyan)
    d.text((490, 614), "SPAN  100 MHz", font=font(23), fill=cyan)
    d.text((944, 614), "STOP  2.500 GHz", font=font(23), fill=cyan)
    d.text((40, 669), "RBW 100 kHz     VBW 300 kHz     REF -30 dBm", font=font(19), fill=muted)
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    im.save(out)
    print(f"Created fictional spectrum display: {out} ({W}x{H})")

if __name__=="__main__":
    main()
