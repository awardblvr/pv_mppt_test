# pv_mppt_test

Test MPPT on Solar Panels with [Kunkin KP184](https://www.amazon.com/Electronic-Battery-Capacity-Internal-Resistance/dp/B076Q8PX5T) ([review](https://www.youtube.com/watch?v=mPRSRuvg3M8))

OK So.. This is not like all the fancy algorithms created by scientists:

[https://www.sciencedirect.com/science/article/abs/pii/S096014811500244X](https://www.sciencedirect.com/science/article/abs/pii/S096014811500244X),

[https://www.electronicdesign.com/technologies/test-measurement/article/21790981/a-photovoltaic-mppt-algorithm-for-dc-electronic-loads](https://www.electronicdesign.com/technologies/test-measurement/article/21790981/a-photovoltaic-mppt-algorithm-for-dc-electronic-loads)

and many more...

It is simple test which starts the load resistance very high to catch VOC.  Then drops it down to 50 Ohms or so, and reads voltage, current and calculates the wattage.. Then drops the load resistance by 1/2 ohm and does it all again, recordig the load resistance, voltage, curremt, and the calculated wattage.. This is my form of MPPT calculation.. Hopefully others will correct me with suggestions or improvements.. But, it SEEMS to kinda work and the results seem pretty close to the ELEJOY [WS400A Solar Panel MPPT Tester](https://www.amazon.com/s?k=WS400A&ref=nb_sb_noss_2)  (or cheaply on Aliexpress: [WS400A](https://www.aliexpress.com/wholesale?catId=0&initiative_id=SB_20210915161626&SearchText=WS400A).)

It produces a .CSV file in OUTDIR (See code) with the date stamp and  panel S/N...   (Used [barcodetopc.com](https://barcodetopc.com) and the IOS app "[Barcode to PC: WiFi Scanner](https://apps.apple.com/app/id1180168368)" to scan panel S/N sticker and enter it into the prompt, after which testing begins... Takes a couple minutes per panel).   You may havbe to modify the port name a bit to get it to find your USB Serial port device.)

Feel free to use it and advise why it is wrong, if so.

NOTE.. The checksum calculation is REQUIRED to send commands to the KP184.. The manual is WRONG in their calculation..  It is CORRECT in my code and you can see what the difference is in Get_CRC16RTU().

```Volts,volts,amps,watts,state,mode_str,panelSN,resistance,timestamp
44.543,44.543,0.0,0.0,0,CR,B41J00052894,100000,20210913_112215.16
43.542,43.542,1.086,47.29,1,CR,B41J00052894,40.0,20210913_112216.53
43.523,43.523,1.1,47.88,1,CR,B41J00052894,39.5,20210913_112217.62
43.504,43.504,1.114,48.46,1,CR,B41J00052894,39.0,20210913_112218.71
43.48,43.48,1.128,49.05,1,CR,B41J00052894,38.5,20210913_112219.81
43.46,43.46,1.142,49.63,1,CR,B41J00052894,38.0,20210913_112220.90
43.441,43.441,1.157,50.26,1,CR,B41J00052894,37.5,20210913_112221.99
43.418,43.418,1.172,50.89,1,CR,B41J00052894,37.0,20210913_112223.09
43.396,43.396,1.187,51.51,1,CR,B41J00052894,36.5,20210913_112224.18
43.375,43.375,1.203,52.18,1,CR,B41J00052894,36.0,20210913_112225.28
43.353,43.353,1.22,52.89,1,CR,B41J00052894,35.5,20210913_112226.37
43.331,43.331,1.236,53.56,1,CR,B41J00052894,35.0,20210913_112227.46
43.306,43.306,1.254,54.31,1,CR,B41J00052894,34.5,20210913_112228.55
43.282,43.282,1.271,55.01,1,CR,B41J00052894,34.0,20210913_112229.64
43.254,43.254,1.29,55.8,1,CR,B41J00052894,33.5,20210913_112230.74
43.227,43.227,1.309,56.58,1,CR,B41J00052894,33.0,20210913_112231.83
43.202,43.202,1.327,57.33,1,CR,B41J00052894,32.5,20210913_112232.92
43.178,43.178,1.347,58.16,1,CR,B41J00052894,32.0,20210913_112234.02
43.151,43.151,1.368,59.03,1,CR,B41J00052894,31.5,20210913_112235.11
43.125,43.125,1.389,59.9,1,CR,B41J00052894,31.0,20210913_112236.20
43.098,43.098,1.411,60.81,1,CR,B41J00052894,30.5,20210913_112237.29
43.067,43.067,1.434,61.76,1,CR,B41J00052894,30.0,20210913_112238.38
43.034,43.034,1.457,62.7,1,CR,B41J00052894,29.5,20210913_112239.48
43.001,43.001,1.481,63.68,1,CR,B41J00052894,29.0,20210913_112240.57
42.969,42.969,1.506,64.71,1,CR,B41J00052894,28.5,20210913_112241.66
42.935,42.935,1.532,65.78,1,CR,B41J00052894,28.0,20210913_112242.75
42.901,42.901,1.559,66.88,1,CR,B41J00052894,27.5,20210913_112243.84
42.865,42.865,1.585,67.94,1,CR,B41J00052894,27.0,20210913_112244.93
42.832,42.832,1.614,69.13,1,CR,B41J00052894,26.5,20210913_112246.02
42.794,42.794,1.644,70.35,1,CR,B41J00052894,26.0,20210913_112247.11
42.758,42.758,1.676,71.66,1,CR,B41J00052894,25.5,20210913_112248.20
42.715,42.715,1.707,72.91,1,CR,B41J00052894,25.0,20210913_112249.29
42.674,42.674,1.74,74.25,1,CR,B41J00052894,24.5,20210913_112250.39
42.627,42.627,1.775,75.66,1,CR,B41J00052894,24.0,20210913_112251.48
42.586,42.586,1.811,77.12,1,CR,B41J00052894,23.5,20210913_112252.58
42.536,42.536,1.848,78.61,1,CR,B41J00052894,23.0,20210913_112253.67
42.487,42.487,1.887,80.17,1,CR,B41J00052894,22.5,20210913_112254.75
42.438,42.438,1.927,81.78,1,CR,B41J00052894,22.0,20210913_112255.84
42.39,42.39,1.969,83.47,1,CR,B41J00052894,21.5,20210913_112256.94
42.335,42.335,2.014,85.26,1,CR,B41J00052894,21.0,20210913_112258.03
42.274,42.274,2.061,87.13,1,CR,B41J00052894,20.5,20210913_112259.13
42.218,42.218,2.109,89.04,1,CR,B41J00052894,20.0,20210913_112300.21
42.151,42.151,2.16,91.05,1,CR,B41J00052894,19.5,20210913_112301.31
42.085,42.085,2.213,93.13,1,CR,B41J00052894,19.0,20210913_112302.40
42.019,42.019,2.27,95.38,1,CR,B41J00052894,18.5,20210913_112303.49
41.934,41.934,2.328,97.62,1,CR,B41J00052894,18.0,20210913_112304.58
41.853,41.853,2.39,100.03,1,CR,B41J00052894,17.5,20210913_112305.67
41.77,41.77,2.456,102.59,1,CR,B41J00052894,17.0,20210913_112306.77
41.687,41.687,2.525,105.26,1,CR,B41J00052894,16.5,20210913_112307.86
41.592,41.592,2.598,108.06,1,CR,B41J00052894,16.0,20210913_112308.96
41.485,41.485,2.676,111.01,1,CR,B41J00052894,15.5,20210913_112310.05
41.376,41.376,2.758,114.12,1,CR,B41J00052894,15.0,20210913_112311.14
41.257,41.257,2.844,117.33,1,CR,B41J00052894,14.5,20210913_112312.24
41.121,41.121,2.936,120.73,1,CR,B41J00052894,14.0,20210913_112313.33
40.975,40.975,3.034,124.32,1,CR,B41J00052894,13.5,20210913_112314.42
40.816,40.816,3.139,128.12,1,CR,B41J00052894,13.0,20210913_112315.51
40.643,40.643,3.25,132.09,1,CR,B41J00052894,12.5,20210913_112316.61
40.447,40.447,3.369,136.27,1,CR,B41J00052894,12.0,20210913_112317.70
40.225,40.225,3.497,140.67,1,CR,B41J00052894,11.5,20210913_112318.79
39.978,39.978,3.634,145.28,1,CR,B41J00052894,11.0,20210913_112319.87
39.695,39.695,3.78,150.05,1,CR,B41J00052894,10.5,20210913_112320.97
39.366,39.366,3.936,154.94,1,CR,B41J00052894,10.0,20210913_112322.06
38.996,38.996,4.103,160.0,1,CR,B41J00052894,9.5,20210913_112323.16
38.549,38.549,4.282,165.07,1,CR,B41J00052894,9.0,20210913_112324.25
38.011,38.011,4.471,169.95,1,CR,B41J00052894,8.5,20210913_112325.34
37.343,37.343,4.668,174.32,1,CR,B41J00052894,8.0,20210913_112326.43
36.489,36.489,4.866,177.56,1,CR,B41J00052894,7.5,20210913_112327.52
35.39,35.39,5.054,178.86,1,CR,B41J00052894,7.0,20210913_112328.61
23.576,23.576,3.696,87.14,1,CR,B41J00052894,6.5,20210913_112329.71
24.161,24.161,3.735,90.24,1,CR,B41J00052894,6.0,20210913_112330.80
24.038,24.038,3.903,93.82,1,CR,B41J00052894,5.5,20210913_112331.89
22.459,22.459,3.865,86.8,1,CR,B41J00052894,5.0,20210913_112332.99
20.669,20.669,3.835,79.27,1,CR,B41J00052894,4.5,20210913_112334.08
```
