#!/bin/sh

if [ -e /var/lib/baogw/howcom_old ]; then
    rm /var/lib/baogw/howcom_old
    echo 'フラグファイル"howcom_old"を削除しました'
else
    echo 'フラグファイル"howcom_old"は既に削除されています'
fi

exit 0