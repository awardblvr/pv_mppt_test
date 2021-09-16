# pv_mppt_test

Test MPPT on Solar Panels with Kunkin KP184

OK So.. This is not like all the fancy algorithms created by scientists:

[https://www.sciencedirect.com/science/article/abs/pii/S096014811500244X](https://www.sciencedirect.com/science/article/abs/pii/S096014811500244X),

[https://www.electronicdesign.com/technologies/test-measurement/article/21790981/a-photovoltaic-mppt-algorithm-for-dc-electronic-loads](https://www.electronicdesign.com/technologies/test-measurement/article/21790981/a-photovoltaic-mppt-algorithm-for-dc-electronic-loads)

and many more...

It is simple test which starts the load resistance very high to catch VOC.  Then drops it down to 50Ohms or so,  and readfs voltage, current and calcuates the wattage.. Then drops the load resistance by 1/2 ohm and does it all again, recordig the load resistance, voltage, curremt, and the calculated wattage.. This is my form of MPPT calculation.. Hopefully others will correct me with suggestions fvor improvements.. Buit it SEEMS to kinda work and the results seem pretty close to the ELEJOY [WS400A Solar Panel MPPT Tester](https://www.amazon.com/s?k=WS400A&ref=nb_sb_noss_2)   or cheaply on Aliexpress: [WS400A](https://www.aliexpress.com/wholesale?catId=0&initiative_id=SB_20210915161626&SearchText=WS400A).

It produces a CSV file in OUTDIR (See code) with the date stamp and  panel S/N...   (Used [barcodetopc.com](https://barcodetopc.com) and the IOS app "[Barcode to PC: WiFi Scanner](https://apps.apple.com/app/id1180168368)" to scan panel S/N sticker and enter it into the prompt, after which testing begins... Takes a couple minutes per panel).   You may havbe to modify the port name a bit to get it to find your USB Serial port device.)

Feel free to use it and advise why it is wrong, if so.
