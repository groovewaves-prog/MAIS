#!/bin/sh

if [ -e /var/lib/baogw/Kddi_Miyazaki ]; then
    rm /var/lib/baogw/Kddi_Miyazaki
    echo 'フラグファイル"Kddi_Miyazaki"を削除しました'
else
    echo 'フラグファイル"Kddi_Miyazaki"は既に削除されています'
fi

exit 0