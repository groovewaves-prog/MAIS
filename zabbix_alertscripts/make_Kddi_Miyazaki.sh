#!/bin/sh

if [ -e /var/lib/baogw/Kddi_Miyazaki ]; then
    echo 'フラグファイル"Kddi_Miyazaki"は既に作成されています'
else
    touch /var/lib/baogw/Kddi_Miyazaki
    echo 'フラグファイル"Kddi_Miyazaki"を作成しました'
fi

exit 0