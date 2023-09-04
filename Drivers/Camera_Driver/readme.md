# Camera Module

DLL Files have to be in the directory of the tisgrabber.py file

For more Information on how to Install the necessary drivers for the IC Camera, please refer to the [Installation Guide](../../INSTALL.md).

## Reference

Adapted from [this Repo](https://github.com/TheImagingSource/IC-Imaging-Control-Samples)

## Other Information

### Size per Pixel

|  Mag  | Calibration |  Area @ 1920 x 1200   | Measured Calibration | Image Area @ 1920 x 1200 |
| :---: | :---------: | :-------------------: | :------------------: | :----------------------: |
| 2.5x  | 2.345 μm/px | 4.5024 mm x 2.8140 mm |     3.0754 μm/px     |  5.9048 mm x 3.6905 mm   |
|  5x   | 1.172 μm/px | 2.2502 mm x 1.4064 mm |    ~ 1.5377 μm/px    |  2.9524 mm x 1.8452 mm   |
|  20x  | 0.293 μm/px | 0.5626 mm x 0.3516 mm |    ~ 0.3844 μm/px    |  0.7380 mm x 0.4613 mm   |
|  50x  | 0.118 μm/px | 0.2266 mm x 0.1416 mm |    ~ 0.1538 μm/px    |  0.2953 mm x 0.1846 mm   |
| 100x  | 0.058 μm/px | 0.1114 mm x 0.0696 mm |    ~ 0.0769 μm/px    |   0.1476 mm x 0.092 mm   |

### Pictures per Magnification @ Full area Scan

Approx. Time per Image without Operations: ~ 1.3 s

Approx. Size per Image: ~2.5 MB

|  Mag  | Approx. Num Images | Approx. Time | Approx. Size on HDD |
| :---: | :----------------: | :----------: | :-----------------: |
| 2.5x  |        ~460        |  ~00:09:58   |       1.15 GB       |
|  5x   |       ~1800        |  ~00:39:00   |       4.5 GB        |
|  20x  |       ~29400       |  ~10:37:00   |       73.5 GB       |
|  50x  |      ~185000       |      -       |          -          |
| 100x  |      ~670000       |      -       |          -          |