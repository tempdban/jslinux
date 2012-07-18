#!/bin/bash

rm hda*; split -a9 -d -b 65536 image.img hda && rename 's/$/.bin/' hda*
